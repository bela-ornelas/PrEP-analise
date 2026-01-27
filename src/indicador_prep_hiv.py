import pandas as pd
import numpy as np
import sys
import os
import argparse
import glob
from datetime import datetime
import shutil

# Adicionar diretório raiz ao path
sys.path.append(os.getcwd())

from src.cleaning import clean_disp_df, process_cadastro
from src.preprocessing import enrich_disp_data

# Configurações de Caminhos (Padrão Rede)
PATH_PVHA_DEFAULT = "//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PVHA_prim_ult.parquet"
PATH_IBGE_DEFAULT = "M:/Arquivos Atuais/Tabelas IBGE/Tabela_IBGE_UF e Municípios.xlsx"
PATH_OUTPUT_DEFAULT = "V:/2026/Monitoramento e Avaliação/DOCUMENTOS/PrEP/Indicador PrEP HIV"

def load_data(path_pvha, path_ibge):
    print(f"\n--- 1. CARREGANDO BASES ---")
    
    # 1. PrEP
    df_disp = pd.DataFrame()
    df_cad = pd.DataFrame()
    try:
        list_of_files = glob.glob('.cache/*.pkl')
        if list_of_files:
            latest_file = max(list_of_files, key=os.path.getctime)
            print(f"   Cache encontrado: {latest_file}")
            dados_cache = pd.read_pickle(latest_file)
            df_disp = dados_cache.get('Disp', pd.DataFrame())
            df_cad = dados_cache.get('Cadastro_PrEP', dados_cache.get('Cadastro', pd.DataFrame()))
            print(f"   Bases PrEP carregadas.")
    except Exception as e:
        print(f"   Erro ao ler cache: {e}")

    # 2. PVHA
    df_pvha = pd.DataFrame()
    pop_ibge = pd.DataFrame()
    try:
        if os.path.exists(path_pvha):
            df_pvha = pd.read_parquet(path_pvha)
        elif os.path.exists("PVHA_prim_ult.parquet"):
            df_pvha = pd.read_parquet("PVHA_prim_ult.parquet")
            
        if not df_pvha.empty:
            if 'Populacao_resid' in df_pvha.columns and 'codigo_ibge_resid' in df_pvha.columns:
                pop_ibge = (
                    df_pvha[['Populacao_resid', 'codigo_ibge_resid']]
                    .drop_duplicates(subset='codigo_ibge_resid')
                    .dropna(subset=['codigo_ibge_resid'])
                    .copy()
                )
                pop_ibge['Populacao_resid'] = pop_ibge['Populacao_resid'].astype(int)
                pop_ibge['codigo_ibge_resid'] = pop_ibge['codigo_ibge_resid'].astype(int).astype(str)
                print(f"   População extraída da base PVHA.")

            df_pvha = df_pvha.rename(columns={"reg_res": "regiao_Res", "uf_res": "UF_Res"})
            if 'capital_res' in df_pvha.columns:
                df_pvha['capital_res'] = df_pvha['capital_res'].replace('Porte Alegre', 'Porto Alegre')
            
            if "Menor Data" not in df_pvha.columns and "data_min" in df_pvha.columns:
                df_pvha["Menor Data"] = pd.to_datetime(df_pvha["data_min"], errors="coerce")
            
            print(f"   Base PVHA carregada e tratada.")
    except Exception as e:
        print(f"   Erro ao ler PVHA: {e}")

    # 3. IBGE
    df_ibge = pd.DataFrame()
    try:
        if os.path.exists(path_ibge):
            df_ibge = pd.read_excel(path_ibge)
            print(f"   Base IBGE carregada.")
    except: pass

    return df_disp, df_cad, df_pvha, df_ibge, pop_ibge

def calcular_numerador_prep(df_disp_raw, df_cad, df_pvha, data_fechamento):
    print(f"\n--- 2. CALCULANDO NUMERADOR (Usuários PrEP Ativos) ---")
    df_disp, df_disp_semdupl = clean_disp_df(df_disp_raw, data_fechamento)
    df_cad = process_cadastro(df_cad)
    
    id_col = 'Cod_unificado' if 'Cod_unificado' in df_cad.columns else 'codigo_paciente'
    cols_cad = ['codigo_pac_eleito', 'codigo_ibge_resid']
    if id_col in df_cad.columns: cols_cad.append(id_col)
    
    df = pd.merge(df_disp_semdupl, df_cad[cols_cad], on='codigo_pac_eleito', how='left')
    df['mun_final'] = df['codigo_ibge_resid'].fillna(df['cod_ibge_udm'])
    df['mun_final'] = pd.to_numeric(df['mun_final'], errors='coerce').fillna(0).astype(int).astype(str)
    df = df[df['mun_final'] != '0']
    
    if id_col in df.columns:
        obito_map = df_pvha.dropna(subset=['Cod_unificado', 'data_obito']).drop_duplicates('Cod_unificado')
        obito_map = obito_map.set_index('Cod_unificado')['data_obito']
        df['dt_obito'] = df[id_col].map(obito_map)
        df['dt_obito'] = pd.to_datetime(df['dt_obito'], errors='coerce')
    else:
        df['dt_obito'] = pd.to_datetime(np.nan)

    df = df[df['dt_obito'].isna()]
    df['data_dispensa'] = pd.to_datetime(df['data_dispensa'], errors='coerce').dt.normalize()
    df['duracao'] = pd.to_numeric(df['duracao'], errors='coerce').fillna(30)
    
    df = df.groupby(['codigo_pac_eleito', 'data_dispensa']).agg({'duracao': 'sum', 'mun_final': 'first'}).reset_index()
    df.rename(columns={'duracao': 'duracao_sum'}, inplace=True)
    df['valid_until'] = df['data_dispensa'] + pd.to_timedelta(df['duracao_sum'] * 1.4, unit='D')
    
    start_date = pd.to_datetime("2022-01-01")
    hoje = pd.to_datetime(data_fechamento)
    dates = pd.date_range(start=start_date, end=hoje, freq='ME')
    results = []
    
    arr_pac = df['codigo_pac_eleito'].values
    arr_disp = df['data_dispensa'].values.astype('datetime64[D]')
    arr_valid = df['valid_until'].values.astype('datetime64[D]')
    arr_mun = df['mun_final'].values
    
    for date_ref in dates:
        date_ref_np = date_ref.to_datetime64()
        start_12m_np = (date_ref - pd.DateOffset(years=1)).to_datetime64()
        mask = (arr_valid >= date_ref_np) & (arr_disp <= date_ref_np) & (arr_disp > start_12m_np)
        if not np.any(mask):
            s = pd.Series(dtype=int); s.name = date_ref; results.append(s); continue
        temp_df = pd.DataFrame({'pac': arr_pac[mask], 'mun': arr_mun[mask]})
        counts = temp_df.drop_duplicates(subset='pac', keep='last')['mun'].value_counts()
        counts.name = date_ref; results.append(counts)

    return pd.concat(results, axis=1).fillna(0) if results else pd.DataFrame()

def calcular_denominador_hiv(df_pvha, data_fechamento):
    print(f"\n--- 3. CALCULANDO DENOMINADOR (Novos Vinculados HIV 6m) ---")
    if df_pvha.empty: return pd.DataFrame()
    df = df_pvha.dropna(subset=['Menor Data', 'codigo_ibge_resid']).copy()
    df['codigo_ibge_resid'] = df['codigo_ibge_resid'].astype(int).astype(str)
    df = df.sort_values('Menor Data', ascending=False)
    
    dates = pd.date_range(start="2022-01-01", end=pd.to_datetime(data_fechamento), freq='ME')
    results = []
    for date_ref in dates:
        date_ref_np = date_ref.to_datetime64()
        start_6m_np = (date_ref - pd.DateOffset(months=6)).to_datetime64()
        mask = (df['Menor Data'].values.astype('datetime64[D]') > start_6m_np) & (df['Menor Data'].values.astype('datetime64[D]') <= date_ref_np)
        if not np.any(mask):
            s = pd.Series(dtype=int); s.name = date_ref; results.append(s); continue
        temp_df = df[mask][['Cod_unificado', 'codigo_ibge_resid']] if 'Cod_unificado' in df.columns else df[mask][['codigo_ibge_resid']]
        counts = temp_df.drop_duplicates(keep='first')['codigo_ibge_resid'].value_counts()
        counts.name = date_ref; results.append(counts)
    return pd.concat(results, axis=1).fillna(0) if results else pd.DataFrame()

def classificar_grupo_mun(row):
    vinc, prep, ind = row.get('Vinculados', 0), row.get('Em PrEP', 0), row.get('Indicador_Mun', 0)
    if vinc == 0 and prep == 0: return 'Sem novos vinculados e sem PrEP'
    if vinc == 0 and prep >= 1: return 'Sem novos vinculados, com pessoas em PrEP'
    if ind < 1: return 'Grupo 0'
    if ind < 2: return 'Grupo 1'
    if ind < 3: return 'Grupo 2'
    if ind < 4: return 'Grupo 3'
    return 'Grupo 4'

def classificar_grupo_uf(row):
    vinc, prep, ind = row.get('Vinculados_UF', 0), row.get('Em PrEP_UF', 0), row.get('Indicador_UF', 0)
    if vinc == 0 and prep == 0: return 'Sem novos vinculados e sem PrEP'
    if vinc == 0 and prep >= 1: return 'Sem novos vinculados, com pessoas em PrEP'
    if ind < 1: return 'Grupo 0'
    if ind < 2: return 'Grupo 1'
    if ind < 3: return 'Grupo 2'
    if ind < 4: return 'Grupo 3'
    return 'Grupo 4'

def gerar_tabela_resumo(series_grupo, nome_col_qtd):
    """Gera tabela de contagem, porcentagem e total ordenado."""
    contagem = series_grupo.value_counts()
    ordem_desejada = ["Sem novos vinculados e sem PrEP", 'Sem novos vinculados, com pessoas em PrEP', 
                      "Grupo 0", "Grupo 1", "Grupo 2", "Grupo 3", "Grupo 4"]
    
    porcentagem = (contagem / contagem.sum()) * 100
    df = pd.DataFrame({nome_col_qtd: contagem, '%': porcentagem.round(1)})
    
    # Reordenar e preencher faltantes com 0
    df = df.reindex(ordem_desejada).fillna(0)
    df[nome_col_qtd] = df[nome_col_qtd].astype(int)
    
    # Linha Total
    total = df[nome_col_qtd].sum()
    linha_total = pd.DataFrame({nome_col_qtd: [total], '%': [100]}, index=['Total'])
    
    # Garantir tipo Int64 para suportar NA se houver, mas aqui deve estar limpo
    resumo = pd.concat([df, linha_total])
    return resumo

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_fechamento", required=True)
    parser.add_argument("--path_pvha", default=PATH_PVHA_DEFAULT)
    parser.add_argument("--path_ibge", default=PATH_IBGE_DEFAULT)
    parser.add_argument("--output_dir", default=PATH_OUTPUT_DEFAULT)
    args = parser.parse_args()
    
    dt_fechamento = pd.to_datetime(args.data_fechamento)
    mes, ano = dt_fechamento.month, dt_fechamento.year
    
    df_disp_raw, df_cad, df_pvha, df_ibge, pop_ibge = load_data(args.path_pvha, args.path_ibge)
    
    numerador = calcular_numerador_prep(df_disp_raw, df_cad, df_pvha, args.data_fechamento)
    denominador = calcular_denominador_hiv(df_pvha, args.data_fechamento)
    
    if not numerador.empty and not denominador.empty:
        if not df_ibge.empty:
            df_ibge['codigo_ibge_resid'] = df_ibge['codigo_ibge_resid'].astype(str).str.replace('.0', '', regex=False)
            all_muns = df_ibge['codigo_ibge_resid'].unique()
            map_ibge = df_ibge.set_index('codigo_ibge_resid')
        else:
            all_muns = numerador.index.union(denominador.index)
            map_ibge = pd.DataFrame()

        num_aligned = numerador.reindex(index=all_muns, columns=numerador.columns.union(denominador.columns), fill_value=0)
        den_aligned = denominador.reindex(index=all_muns, columns=num_aligned.columns, fill_value=0)
        
        last_date = num_aligned.columns[-1]
        Indicador = pd.DataFrame({'codigo_ibge_resid': all_muns, 'Em PrEP': num_aligned[last_date].values, 'Vinculados': den_aligned[last_date].values})
        
        if not map_ibge.empty:
            col_uf = next((c for c in map_ibge.columns if c.lower() == 'uf'), 'UF')
            col_reg = next((c for c in map_ibge.columns if 'regia' in c.lower()), 'Região')
            col_nome = next((c for c in map_ibge.columns if 'nome' in c.lower() or 'municip' in c.lower()), 'nome_mun')
            Indicador['Município'] = Indicador['codigo_ibge_resid'].map(map_ibge[col_nome]).fillna('Desconhecido')
            Indicador['UF_Res'] = Indicador['codigo_ibge_resid'].map(map_ibge[col_uf]).fillna('Ign')
            Indicador['regiao_Res'] = Indicador['codigo_ibge_resid'].map(map_ibge[col_reg]).fillna('Ign')
        
        if not pop_ibge.empty:
            Indicador = Indicador.merge(pop_ibge, on='codigo_ibge_resid', how='left').fillna({'Populacao_resid': 0})
        else:
            Indicador['Populacao_resid'] = 0

        # Indicador Município e Grupo
        Indicador['Indicador_Mun'] = Indicador.apply(lambda x: round(x['Em PrEP']/x['Vinculados'], 2) if x['Vinculados'] > 0 else 0, axis=1)
        Indicador['Grupo'] = Indicador.apply(classificar_grupo_mun, axis=1)
        
        # Indicador UF e Grupo
        Indicador['Vinculados_UF'] = Indicador.groupby(["UF_Res"])['Vinculados'].transform('sum')
        Indicador['Em PrEP_UF'] = Indicador.groupby(["UF_Res"])['Em PrEP'].transform('sum')
        Indicador["Indicador_UF"] = (Indicador["Em PrEP_UF"]/Indicador["Vinculados_UF"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
        
        # DF Único de UF para classificação
        Indicador_UF_Unique = Indicador.drop_duplicates("UF_Res")[["UF_Res","Vinculados_UF","Em PrEP_UF","Indicador_UF"]].copy()
        Indicador_UF_Unique['Grupo'] = Indicador_UF_Unique.apply(classificar_grupo_uf, axis=1)

        # --- GERAR TABELAS RESUMO ---
        tabela_geral_UF = gerar_tabela_resumo(Indicador_UF_Unique['Grupo'], 'Qtd UF')
        tabela_geral_mun = gerar_tabela_resumo(Indicador['Grupo'], 'Qtd municípios')
        tabela_mun_50k = gerar_tabela_resumo(Indicador[Indicador['Populacao_resid'] >= 50000]['Grupo'], 'Qtd municípios >=50.000 hab')
        
        # Outras tabelas de apoio
        Indicador_UF_Final = Indicador_UF_Unique.sort_values('UF_Res')
        Indicador_Reg = Indicador.groupby('regiao_Res')[['Vinculados', 'Em PrEP']].sum().reset_index()
        Indicador_Reg['Indicador_Reg'] = (Indicador_Reg['Em PrEP'] / Indicador_Reg['Vinculados']).fillna(0).round(2)
        Indicador_Nac = pd.DataFrame(Indicador[['Vinculados', 'Em PrEP']].sum()).T
        Indicador_Nac['Indicador_Nac'] = (Indicador_Nac['Em PrEP'] / Indicador_Nac['Vinculados']).fillna(0).round(2)
        
        Indicador_mes_mun = num_aligned.div(den_aligned).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
        Indicador_mes = (num_aligned.sum() / den_aligned.sum()).fillna(0).round(2).to_frame(name='Brasil')
        
        filename = f"Indicador_PrEP_{mes}_{ano}.xlsx"
        print(f"Salvando arquivo: {filename} ...")
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Aba Geral
                tabela_geral_UF.to_excel(writer, sheet_name="Geral")
                tabela_geral_mun.to_excel(writer, sheet_name="Geral", startrow=len(tabela_geral_UF) + 3)
                tabela_mun_50k.to_excel(writer, sheet_name="Geral", startrow=len(tabela_geral_UF) + 3 + len(tabela_geral_mun) + 3)
                
                # Demais Abas
                cols_mun = ['regiao_Res', 'UF_Res', 'codigo_ibge_resid','Município','Populacao_resid','Vinculados', 'Em PrEP','Indicador_Mun','Grupo']
                Indicador[cols_mun].to_excel(writer, sheet_name="Município", index=False)
                Indicador[Indicador["Populacao_resid"] >= 50000][cols_mun].to_excel(writer, sheet_name="Município_50k", index=False)
                Indicador_UF_Final.to_excel(writer, sheet_name="UF", index=False)
                Indicador_Reg.to_excel(writer, sheet_name="Região", index=False)
                Indicador_Nac.to_excel(writer, sheet_name="Nacional", index=False)
                Indicador_mes.to_excel(writer, sheet_name="Mensal")
                Indicador_mes_mun.to_excel(writer, sheet_name="Mensal_municipio")
            
            if os.path.exists(args.output_dir):
                shutil.copy2(filename, os.path.join(args.output_dir, filename))
                print(f"Cópia salva na rede: {os.path.join(args.output_dir, filename)}")
        except Exception as e:
            print(f"Erro ao salvar: {e}")

if __name__ == "__main__":
    main()