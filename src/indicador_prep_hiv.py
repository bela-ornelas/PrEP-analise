import pandas as pd
import numpy as np
import sys
import os
import argparse
import glob
from datetime import datetime

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
    
    # 1. PrEP (DISPENSAÇÕES E CADASTRO DO CACHE)
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
    try:
        if os.path.exists(path_pvha):
            df_pvha = pd.read_parquet(path_pvha)
        elif os.path.exists("PVHA_prim_ult.parquet"):
            df_pvha = pd.read_parquet("PVHA_prim_ult.parquet")
            
        if not df_pvha.empty:
            df_pvha["Menor Data"] = pd.to_datetime(df_pvha["data_min"], errors="coerce")
            print(f"   Base PVHA carregada.")
    except Exception as e:
        print(f"   Erro ao ler PVHA: {e}")

    # 3. IBGE
    df_ibge = pd.DataFrame()
    try:
        if os.path.exists(path_ibge):
            df_ibge = pd.read_excel(path_ibge)
    except: pass

    return df_disp, df_cad, df_pvha, df_ibge

def calcular_numerador_prep(df_disp_raw, df_cad, df_pvha, data_fechamento):
    print(f"\n--- 2. CALCULANDO NUMERADOR (Usuários PrEP Ativos) ---")
    
    # 1. Limpeza e Processamento Padrão do Projeto
    df_disp, df_disp_semdupl = clean_disp_df(df_disp_raw, data_fechamento)
    df_cad = process_cadastro(df_cad)
    
    # 2. Enriquecimento (Trazer IBGE Residência e Dados HIV para exclusão)
    print("    Cruzando dados para identificar e excluir usuários que se tornaram PVHA...")
    
    # Identificar coluna de código unificado
    id_col = 'Cod_unificado' if 'Cod_unificado' in df_cad.columns else 'codigo_paciente'
    
    # Unir residência e identificador nas dispensas
    cols_cad = ['codigo_pac_eleito', 'codigo_ibge_resid']
    if id_col in df_cad.columns: cols_cad.append(id_col)
    
    df = pd.merge(df_disp_semdupl, df_cad[cols_cad], on='codigo_pac_eleito', how='left')
    
    # Regra IBGE: Residência > UDM
    df['mun_final'] = df['codigo_ibge_resid'].fillna(df['cod_ibge_udm'])
    df['mun_final'] = pd.to_numeric(df['mun_final'], errors='coerce').fillna(0).astype(int).astype(str)
    df = df[df['mun_final'] != '0']
    
    # Mapear data Óbito (Exclusão única permitida pelo notebook)
    if id_col in df.columns:
        obito_map = df_pvha.dropna(subset=['Cod_unificado', 'data_obito']).drop_duplicates('Cod_unificado')
        obito_map = obito_map.set_index('Cod_unificado')['data_obito']
        df['dt_obito'] = df[id_col].map(obito_map)
        df['dt_obito'] = pd.to_datetime(df['dt_obito'], errors='coerce')
    else:
        df['dt_obito'] = pd.to_datetime(np.nan)

    # FILTRO: Excluir apenas ÓBITOS (conforme notebook)
    df = df[df['dt_obito'].isna()]
    print("    Filtro aplicado: Usuários com data de óbito removidos.")

    # 3. Preparação Temporal
    # Normalizar para remover horas e evitar falhas no agrupamento
    df['data_dispensa'] = pd.to_datetime(df['data_dispensa'], errors='coerce').dt.normalize()
    df['duracao'] = pd.to_numeric(df['duracao'], errors='coerce').fillna(30)
    
    # Agrupar dispensas do mesmo dia (duracao_sum)
    # Importante: Agrupar soma as durações de frascos entregues juntos
    df = df.groupby(['codigo_pac_eleito', 'data_dispensa']).agg({
        'duracao': 'sum',
        'mun_final': 'first'
    }).reset_index()
    
    df.rename(columns={'duracao': 'duracao_sum'}, inplace=True)
    
    # Calcular validade da dispensa (Duração Total * 1.4)
    df['valid_until'] = df['data_dispensa'] + pd.to_timedelta(df['duracao_sum'] * 1.4, unit='D')
    
    # Ordenar por data (Crucial para drop_duplicates keep='last')
    df = df.sort_values('data_dispensa')

    # 4. Loop Mensal
    start_date = pd.to_datetime("2022-01-01")
    hoje = pd.to_datetime(data_fechamento)
    dates = pd.date_range(start=start_date, end=hoje, freq='ME')
    results = []
    
    print(f"   Processando {len(dates)} meses...")
    
    # Converter para numpy arrays para performance no loop
    arr_pac = df['codigo_pac_eleito'].values
    arr_disp = df['data_dispensa'].values.astype('datetime64[D]')
    arr_valid = df['valid_until'].values.astype('datetime64[D]')
    arr_mun = df['mun_final'].values
    
    for date_ref in dates:
        date_ref_np = date_ref.to_datetime64()
        start_12m_np = (date_ref - pd.DateOffset(years=1)).to_datetime64()
        
        # Filtros: Ativo (validade >= fim do mês) E Retido (dispensa > 1 ano atrás)
        # Nota: valid_until inclui o dia de referência? Sim, se validade vai até dia 31, cobre dia 31.
        mask = (arr_valid >= date_ref_np) & (arr_disp <= date_ref_np) & (arr_disp > start_12m_np)
        
        if not np.any(mask): continue
            
        # Filtrar subset
        subset_pac = arr_pac[mask]
        subset_mun = arr_mun[mask]
        
        # Deduplicar Paciente (Pega a dispensa mais recente na janela se houver sobreposição)
        # Como arrays vieram de DF ordenado, o último registro de um paciente é o mais recente válido
        temp_df = pd.DataFrame({'pac': subset_pac, 'mun': subset_mun})
        unique_active = temp_df.drop_duplicates(subset='pac', keep='last')
        
        counts = unique_active['mun'].value_counts()
        counts.name = date_ref
        results.append(counts)

    if results:
        return pd.concat(results, axis=1).fillna(0).T
    return pd.DataFrame()

def calcular_denominador_hiv(df_pvha, data_fechamento):
    print(f"\n--- 3. CALCULANDO DENOMINADOR (Novos Vinculados HIV 6m) ---")
    if df_pvha.empty: return pd.DataFrame() 
    
    hoje = pd.to_datetime(data_fechamento)
    start_date = pd.to_datetime("2022-01-01")
    
    # Filtros e Ordenação
    df = df_pvha.dropna(subset=['Menor Data', 'codigo_ibge_resid']).copy()
    df['codigo_ibge_resid'] = df['codigo_ibge_resid'].astype(int).astype(str)
    
    # Ordenar por data decrescente (para bater com lógica do notebook 'keep=first' após sort desc)
    df = df.sort_values('Menor Data', ascending=False)
    
    arr_date = df['Menor Data'].values.astype('datetime64[D]')
    arr_mun = df['codigo_ibge_resid'].values
    arr_id = df['Cod_unificado'].values if 'Cod_unificado' in df.columns else np.arange(len(df))

    dates = pd.date_range(start=start_date, end=hoje, freq='ME')
    results = []

    for date_ref in dates:
        date_ref_np = date_ref.to_datetime64()
        start_6m_np = (date_ref - pd.DateOffset(months=6)).to_datetime64()
        
        # Janela: (Hoje - 6 meses, Hoje]
        mask = (arr_date > start_6m_np) & (arr_date <= date_ref_np)
        
        if not np.any(mask): continue
            
        temp_df = pd.DataFrame({'id': arr_id[mask], 'mun': arr_mun[mask]})
        # Deduplicar ID (Como ordenamos DESC, keep='first' pega o mais recente/primeiro da lista)
        unique_vinc = temp_df.drop_duplicates('id', keep='first')
        
        counts = unique_vinc['mun'].value_counts()
        counts.name = date_ref
        results.append(counts)

    if results:
        return pd.concat(results, axis=1).fillna(0).T
    return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_fechamento", required=True)
    parser.add_argument("--path_pvha", default=PATH_PVHA_DEFAULT)
    parser.add_argument("--path_ibge", default=PATH_IBGE_DEFAULT)
    parser.add_argument("--output_dir", default=PATH_OUTPUT_DEFAULT)
    args = parser.parse_args()
    
    df_disp_raw, df_cad, df_pvha, df_ibge = load_data(args.path_pvha, args.path_ibge)
    
    numerador = calcular_numerador_prep(df_disp_raw, df_cad, df_pvha, args.data_fechamento)
    denominador = calcular_denominador_hiv(df_pvha, args.data_fechamento)
    
    if not numerador.empty and not denominador.empty:
        common_dates = numerador.index.intersection(denominador.index)
        common_muns = numerador.columns.intersection(denominador.columns)
        
        ind = numerador.loc[common_dates, common_muns].div(denominador.loc[common_dates, common_muns])
        ind = ind.replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
        
        final_df = ind.T
        if not df_ibge.empty:
            df_ibge['codigo_ibge_resid'] = df_ibge['codigo_ibge_resid'].astype(str).str.replace('.0', '', regex=False)
            map_nomes = df_ibge.set_index('codigo_ibge_resid')['nome_mun']
            final_df.insert(0, 'Município', final_df.index.map(map_nomes).fillna('Desconhecido'))
        
        final_df.columns = [c.strftime('%b_%Y').lower() if isinstance(c, pd.Timestamp) else c for c in final_df.columns]
        
        output_file = f"Indicador_PrEP_HIV_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        final_df.to_excel(output_file)
        print(f"\n--- SUCESSO! Arquivo gerado: {output_file} ---")
        
        try:
            if not os.path.exists(args.output_dir): os.makedirs(args.output_dir)
            final_df.to_excel(os.path.join(args.output_dir, output_file))
        except: pass
    else:
        print("Erro: Bases insuficientes para cálculo.")

if __name__ == "__main__":
    main()
