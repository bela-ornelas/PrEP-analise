import pandas as pd
import numpy as np
import sys
import os
import argparse
import time
from datetime import datetime
import shutil
from pathlib import Path

# Importar módulo de visualização refatorado
try:
    import visualizacao as viz
    import sociodemografico as socio
except ImportError:
    # Fallback caso execute de fora da pasta
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import visualizacao as viz
    import sociodemografico as socio

# =============================================================================
# CONFIGURAÇÕES E CAMINHOS
# =============================================================================

PATH_PREP_UNICO = r"M:\Arquivos Atuais\Bancos Atuais HIV\Mensais\PrEP_unico.parquet"
PATH_PREP_DISP = r"M:\Arquivos Atuais\Bancos Atuais HIV\Mensais\PrEP_dispensas.parquet"
PATH_PVHA = r"//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PVHA_prim_ult.parquet"
PATH_IBGE = r"M:\Arquivos Atuais\Tabelas IBGE\Tabela_IBGE_UF e Municípios.xlsx"
OUTPUT_DIR = r"V:\2026\Monitoramento e Avaliação\DOCUMENTOS\PrEP\Indicador PrEP HIV"

# Ordem Solicitada
ORDEM_REGIOES = ['Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']

# Mapeamento Fixo IBGE -> Sigla
MAP_UF_SIGLA = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS',
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
}

# =============================================================================
# FUNÇÕES DE CARREGAMENTO
# =============================================================================

def load_data(args):
    """Carrega todas as bases necessárias."""
    print("--- 1. CARREGANDO BASES ---")
    
    if not os.path.exists(args.path_prep): raise FileNotFoundError(f"Arquivo não encontrado: {args.path_prep}")
    df_prep = pd.read_parquet(args.path_prep)
    for col in ['codigo_ibge_resid', 'cod_ibge_udm']:
        if col in df_prep.columns:
            df_prep[col] = pd.to_numeric(df_prep[col], errors='coerce')

    if not os.path.exists(args.path_disp): raise FileNotFoundError(f"Arquivo não encontrado: {args.path_disp}")
    df_disp = pd.read_parquet(args.path_disp)
    
    if not os.path.exists(args.path_pvha): raise FileNotFoundError(f"Arquivo não encontrado: {args.path_pvha}")
    df_pvha = pd.read_parquet(args.path_pvha)
    if "Menor Data" not in df_pvha.columns and "data_min" in df_pvha.columns:
        df_pvha["Menor Data"] = pd.to_datetime(df_pvha["data_min"], errors="coerce")
    
    pop_ibge = pd.DataFrame()
    if 'Populacao_resid' in df_pvha.columns and 'codigo_ibge_resid' in df_pvha.columns:
        pop_ibge = df_pvha[['Populacao_resid', 'codigo_ibge_resid']].drop_duplicates(subset='codigo_ibge_resid').dropna(subset=['codigo_ibge_resid']).copy()
        pop_ibge['Populacao_resid'] = pd.to_numeric(pop_ibge['Populacao_resid'], errors='coerce').fillna(0).astype(int)
        pop_ibge['codigo_ibge_resid'] = pd.to_numeric(pop_ibge['codigo_ibge_resid'], errors='coerce').fillna(0).astype(int).astype(str)

    df_ibge = pd.DataFrame()
    if os.path.exists(args.path_ibge):
        df_ibge = pd.read_excel(args.path_ibge)
        df_ibge["codigo_ibge_resid"] = df_ibge["codigo_ibge_resid"].astype(str).str.replace('.0', '', regex=False)

    return df_prep, df_disp, df_pvha, df_ibge, pop_ibge

# =============================================================================
# CÁLCULO DE SÉRIES HISTÓRICAS
# =============================================================================

def gerar_series_mensais(df_prep, df_disp, df_pvha, data_fechamento):
    print("\n--- GERANDO SÉRIES MENSAIS (MUNICÍPIO) ---")
    start_date = pd.to_datetime("2022-01-01")
    end_date = pd.to_datetime(data_fechamento)
    dates = pd.date_range(start=start_date, end=end_date, freq='ME')
    
    cols_merge = ['codigo_pac_eleito', 'codigo_ibge_resid', 'cod_ibge_udm']
    df_merge = df_disp.merge(df_prep[cols_merge], on='codigo_pac_eleito', how='left', suffixes=('_disp', ''))
    df_merge['mun_final'] = df_merge['codigo_ibge_resid'].fillna(df_merge['cod_ibge_udm'])
    df_merge['mun_final'] = pd.to_numeric(df_merge['mun_final'], errors='coerce').fillna(0).astype(int).astype(str)
    df_merge = df_merge[df_merge['mun_final'] != '0']

    col_duracao = 'duracao_sum' if 'duracao_sum' in df_merge.columns else 'duracao'
    df_merge['duracao_val'] = pd.to_numeric(df_merge[col_duracao], errors='coerce').fillna(30) if col_duracao in df_merge.columns else 30
    df_merge['dt_disp'] = pd.to_datetime(df_merge['dt_disp'], errors='coerce')
    df_merge['valid_until'] = df_merge['dt_disp'] + pd.to_timedelta(df_merge['duracao_val'] * 1.4, unit='D')
    
    arr_pac, arr_mun, arr_disp, arr_valid = df_merge['codigo_pac_eleito'].values, df_merge['mun_final'].values, df_merge['dt_disp'].values.astype('datetime64[D]'), df_merge['valid_until'].values.astype('datetime64[D]')
    prep_results = []
    
    df_pvha_clean = df_pvha.dropna(subset=['Menor Data', 'codigo_ibge_resid']).copy()
    df_pvha_clean['codigo_ibge_resid'] = pd.to_numeric(df_pvha_clean['codigo_ibge_resid'], errors='coerce').fillna(0).astype(int).astype(str)
    arr_pvha_mun, arr_pvha_data = df_pvha_clean['codigo_ibge_resid'].values, df_pvha_clean['Menor Data'].values.astype('datetime64[D]')
    vinc_results = []
    
    print(f"   Calculando mês a mês ({len(dates)} meses)...")
    for date_ref in dates:
        col_name = f"{date_ref.month}_{date_ref.year}"
        date_ref_np = date_ref.to_datetime64()
        
        mask_prep = (arr_valid >= date_ref_np) & (arr_disp <= date_ref_np)
        if np.any(mask_prep):
            temp_df = pd.DataFrame({'pac': arr_pac[mask_prep], 'mun': arr_mun[mask_prep]})
            counts_prep = temp_df.drop_duplicates(subset='pac')['mun'].value_counts()
            counts_prep.name = col_name
            prep_results.append(counts_prep)
        else:
            prep_results.append(pd.Series(name=col_name, dtype=int))
            
        start_6m_np = (date_ref - pd.DateOffset(months=6)).to_datetime64()
        mask_vinc = (arr_pvha_data > start_6m_np) & (arr_pvha_data <= date_ref_np)
        if np.any(mask_vinc):
            counts_vinc = pd.Series(arr_pvha_mun[mask_vinc]).value_counts()
            counts_vinc.name = col_name
            vinc_results.append(counts_vinc)
        else:
            vinc_results.append(pd.Series(name=col_name, dtype=int))

    return pd.concat(prep_results, axis=1).fillna(0).astype(int), pd.concat(vinc_results, axis=1).fillna(0).astype(int)

# =============================================================================
# SÉRIES SOCIODEMOGRÁFICAS
# =============================================================================

def gerar_series_mensais_raca(df_prep, df_disp, df_pvha, df_ibge, data_fechamento):
    """Gera contagens brutas mensais por Regiao e Raça."""
    print("\n   Calculando série histórica mensal por Região e Raça...")
    start_date = pd.to_datetime("2022-01-01")
    end_date = pd.to_datetime(data_fechamento)
    dates = pd.date_range(start=start_date, end=end_date, freq='ME')
    
    col_reg = next((c for c in df_ibge.columns if 'regia' in c.lower()), 'Região')
    map_reg = df_ibge.set_index('codigo_ibge_resid')[col_reg].to_dict()
    
    # PrEP
    cols_prep_needed = ['codigo_pac_eleito', 'raca4_cat', 'codigo_ibge_resid', 'cod_ibge_udm']
    df_m = df_disp.merge(df_prep[[c for c in cols_prep_needed if c in df_prep.columns]], on='codigo_pac_eleito', how='left')
    
    # Garantir que mun seja calculado corretamente mesmo se faltar cod_ibge_udm na base por algum motivo
    if 'cod_ibge_udm' in df_m.columns:
        df_m['mun'] = df_m['codigo_ibge_resid'].fillna(df_m['cod_ibge_udm']).astype(str).str.replace('.0', '', regex=False)
    else:
        df_m['mun'] = df_m['codigo_ibge_resid'].astype(str).str.replace('.0', '', regex=False)
        
    df_m['reg'] = df_m['mun'].map(map_reg).fillna('Ignorada')
    df_m['raca'] = df_m['raca4_cat'].fillna('Ignorada/Não informada')
    df_m['dt_disp'] = pd.to_datetime(df_m['dt_disp'], errors='coerce')
    col_dur = 'duracao_sum' if 'duracao_sum' in df_m.columns else 'duracao'
    df_m['dur_v'] = pd.to_numeric(df_m[col_dur], errors='coerce').fillna(30) if col_dur in df_m.columns else 30
    df_m['valid'] = df_m['dt_disp'] + pd.to_timedelta(df_m['dur_v'] * 1.4, unit='D')
    
    # PVHA
    df_v = df_pvha.dropna(subset=['Menor Data']).copy()
    if 'raca4_cat' not in df_v.columns: df_v = socio.harmonizar_raca_pvha(df_v)
    df_v['reg'] = df_v['codigo_ibge_resid'].astype(str).str.replace('.0', '', regex=False).map(map_reg).fillna('Ignorada')
    df_v['raca'] = df_v['raca4_cat'].fillna('Ignorada/Não informada')
    
    prep_res, vinc_res = [], []
    for d_ref in dates:
        c_n = f"{d_ref.month}_{d_ref.year}"
        d_np = d_ref.to_datetime64()
        # PrEP
        m_p = (df_m['valid'] >= d_np) & (df_m['dt_disp'] <= d_np)
        if np.any(m_p):
            c_p = df_m[m_p].drop_duplicates('codigo_pac_eleito').groupby(['reg', 'raca']).size()
            c_p.name = c_n
            prep_res.append(c_p)
        # Vinc
        s_6 = (d_ref - pd.DateOffset(months=6)).to_datetime64()
        m_v = (df_v['Menor Data'] > s_6) & (df_v['Menor Data'] <= d_np)
        if np.any(m_v):
            c_v = df_v[m_v].groupby(['reg', 'raca']).size()
            c_v.name = c_n
            vinc_res.append(c_v)
            
    return pd.concat(prep_res, axis=1).fillna(0).astype(int), pd.concat(vinc_res, axis=1).fillna(0).astype(int)

# =============================================================================
# AUXILIARES
# =============================================================================

def classificar_grupo_mun(row):
    vinc, prep, ind = row.get('Vinculados', 0), row.get('Em PrEP', 0), row.get('Indicador_Mun', 0)
    if vinc == 0: return 'Sem novos vinculados e sem PrEP' if prep == 0 else 'Sem novos vinculados, com pessoas em PrEP'
    if ind < 1: return 'Grupo 0'
    if ind < 2: return 'Grupo 1'
    if ind < 3: return 'Grupo 2'
    if ind < 4: return 'Grupo 3'
    return 'Grupo 4'

def classificar_grupo_uf(row):
    vinc, prep, ind = row.get('Vinculados_UF', 0), row.get('Em PrEP_UF', 0), row.get('Indicador_UF', 0)
    if vinc == 0: return 'Sem novos vinculados e sem PrEP' if prep == 0 else 'Sem novos vinculados, com pessoas em PrEP'
    if ind < 1: return 'Grupo 0'
    if ind < 2: return 'Grupo 1'
    if ind < 3: return 'Grupo 2'
    if ind < 4: return 'Grupo 3'
    return 'Grupo 4'

def gerar_tabela_resumo(series_grupo, nome_col_qtd):
    contagem = series_grupo.value_counts()
    ordem = ["Sem novos vinculados e sem PrEP", 'Sem novos vinculados, com pessoas em PrEP', "Grupo 0", "Grupo 1", "Grupo 2", "Grupo 3", "Grupo 4"]
    porcentagem = (contagem / contagem.sum()) * 100
    df = pd.DataFrame({nome_col_qtd: contagem, '%': porcentagem.round(1)}).reindex(ordem).fillna(0)
    df[nome_col_qtd] = df[nome_col_qtd].astype(int)
    return pd.concat([df, pd.DataFrame({nome_col_qtd: [df[nome_col_qtd].sum()], '%': [100]}, index=['Total'])])

# =============================================================================
# MAIN
# =============================================================================

def main():
    start_time = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_fechamento", required=True)
    parser.add_argument("--path_prep", default=PATH_PREP_UNICO); parser.add_argument("--path_disp", default=PATH_PREP_DISP)
    parser.add_argument("--path_pvha", default=PATH_PVHA); parser.add_argument("--path_ibge", default=PATH_IBGE)
    parser.add_argument("--output_dir", default=OUTPUT_DIR)
    args = parser.parse_args()
    
    print(f"=== GERADOR INDICADOR PrEP:HIV (OTIMIZADO) ===\nData Fechamento: {args.data_fechamento}")
    dt_fechamento = pd.to_datetime(args.data_fechamento); mes, ano = dt_fechamento.month, dt_fechamento.year
    
    # 1. Load
    df_prep, df_disp, df_pvha, df_ibge, pop_ibge = load_data(args)
    
    # 2. Séries Municipais Brutas
    EmPrEP_Serie_Historica_mun, Vinculados_mun2 = gerar_series_mensais(df_prep, df_disp, df_pvha, args.data_fechamento)
    
    # 3. Consolidar Atual
    print("\n--- CONSOLIDANDO INDICADOR ATUAL ---")
    num_atual = df_prep[df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente']['codigo_ibge_resid'].fillna(df_prep['cod_ibge_udm']).astype(str).str.replace('.0', '', regex=False).value_counts()
    start_6m = dt_fechamento - pd.DateOffset(months=6)
    den_atual = df_pvha[(df_pvha['Menor Data'] > start_6m) & (df_pvha['Menor Data'] <= dt_fechamento)]['codigo_ibge_resid'].astype(str).str.replace('.0', '', regex=False).value_counts()
    
    all_muns = pd.Index(df_ibge['codigo_ibge_resid'].unique()) if not df_ibge.empty else num_atual.index.union(den_atual.index)
    Indicador = pd.DataFrame(index=all_muns); Indicador.index.name = 'codigo_ibge_resid'
    Indicador['Em PrEP'] = num_atual.reindex(all_muns).fillna(0).astype(int)
    Indicador['Vinculados'] = den_atual.reindex(all_muns).fillna(0).astype(int)
    
    if not df_ibge.empty:
        map_ibge = df_ibge.set_index('codigo_ibge_resid')
        col_uf = next((c for c in map_ibge.columns if c.lower() in ['uf', 'sigla_uf', 'sg_uf']), 'UF')
        col_sigla_uf = next((c for c in map_ibge.columns if c.lower() in ['sigla_uf', 'sg_uf', 'uf_sigla']), None)
        col_reg = next((c for c in map_ibge.columns if 'regia' in c.lower()), 'Região')
        candidatos_mun = [c for c in map_ibge.columns if ('nome' in c.lower() or 'municip' in c.lower()) and 'uf' not in c.lower()]
        col_nome = next((c for c in candidatos_mun if c.lower() in ['nome_mun', 'municipio']), candidatos_mun[0] if candidatos_mun else 'nome_mun')
        
        Indicador['Município'] = Indicador.index.map(map_ibge[col_nome]).fillna('Desconhecido')
        Indicador['UF_Res'] = Indicador.index.map(map_ibge[col_uf]).fillna('Ign')
        Indicador['regiao_Res'] = Indicador.index.map(map_ibge[col_reg]).fillna('Ign')
        map_cod_sigla = MAP_UF_SIGLA.copy()
        if col_sigla_uf:
            map_cod_sigla.update(map_ibge[[col_uf, col_sigla_uf]].drop_duplicates().set_index(col_uf)[col_sigla_uf].to_dict())
            Indicador['Sigla_UF'] = Indicador.index.map(map_ibge[col_sigla_uf]).fillna(Indicador['UF_Res'].astype(str).map(MAP_UF_SIGLA)).fillna(Indicador['UF_Res'])
        else:
            Indicador['Sigla_UF'] = Indicador['UF_Res'].astype(str).map(MAP_UF_SIGLA).fillna(Indicador['UF_Res'])
    
    if not pop_ibge.empty: Indicador = Indicador.merge(pop_ibge, on='codigo_ibge_resid', how='left').fillna({'Populacao_resid': 0})
    Indicador['Indicador_Mun'] = Indicador.apply(lambda x: round(x['Em PrEP']/x['Vinculados'], 2) if x['Vinculados'] > 0 else 0, axis=1)
    Indicador['Grupo'] = Indicador.apply(classificar_grupo_mun, axis=1)
    
    Indicador['Vinculados_UF'] = Indicador.groupby("UF_Res")['Vinculados'].transform('sum')
    Indicador['Em PrEP_UF'] = Indicador.groupby("UF_Res")['Em PrEP'].transform('sum')
    Indicador["Indicador_UF"] = (Indicador["Em PrEP_UF"]/Indicador["Vinculados_UF"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    Indicador['Vinculados_Reg'] = Indicador.groupby("regiao_Res")['Vinculados'].transform('sum')
    Indicador['Em PrEP_Reg'] = Indicador.groupby("regiao_Res")['Em PrEP'].transform('sum')
    Indicador["Indicador_Reg"] = (Indicador["Em PrEP_Reg"]/Indicador["Vinculados_Reg"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)

    # Aba Mensal Município
    print("--- PROCESSANDO ABA MENSAL_MUNICIPIO ---")
    map_mun_n = Indicador.set_index(Indicador.index)['Município'].to_dict()
    Indicador_mes_mun = EmPrEP_Serie_Historica_mun.div(Vinculados_mun2).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
    Indicador_mes_mun.insert(0, "nome_mun", Indicador_mes_mun.index.map(map_mun_n))
    cols_m = sorted([c for c in Indicador_mes_mun.columns if c != "nome_mun"], key=lambda x: (int(x.split("_")[1]), int(x.split("_")[0])))
    Indicador_mes_mun = Indicador_mes_mun[["nome_mun"] + cols_m]

    Indicador_UF_Unique = Indicador.drop_duplicates("UF_Res")[["UF_Res", "Sigla_UF", "Vinculados_UF", "Em PrEP_UF", "Indicador_UF"]].copy()
    Indicador_UF_Unique['Grupo'] = Indicador_UF_Unique.apply(classificar_grupo_uf, axis=1).sort_values()
    Indicador_Reg_Unique = Indicador.drop_duplicates("regiao_Res")[["regiao_Res","Vinculados_Reg","Em PrEP_Reg","Indicador_Reg"]].copy()
    Indicador_Reg_Unique['regiao_Res'] = pd.Categorical(Indicador_Reg_Unique['regiao_Res'], categories=ORDEM_REGIOES, ordered=True)
    Indicador_Reg_Unique = Indicador_Reg_Unique.sort_values("regiao_Res")
    Indicador_Nac = pd.DataFrame({"Vinculados": [Indicador['Vinculados'].sum()], "Em PrEP": [Indicador['Em PrEP'].sum()], "Indicador_Nac": [(Indicador['Em PrEP'].sum() / Indicador['Vinculados'].sum()) if Indicador['Vinculados'].sum() > 0 else 0]}, index=["Brasil"]).round(2)

    # Histórico Brasil
    Indicador_mes_BR = EmPrEP_Serie_Historica_mun.sum().div(Vinculados_mun2.sum()).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    df_mes_br = pd.DataFrame(Indicador_mes_BR).T[cols_m]; df_mes_br.index = ['Brasil']

    # 6b. Análise Regional e UF
    print("\n--- CALCULANDO SÉRIES REGIONAIS/UF E TESTES ---")
    df_mk_final = pd.DataFrame()
    if not df_ibge.empty:
        map_reg_s = {str(k): v for k, v in df_ibge.set_index('codigo_ibge_resid')[col_reg].to_dict().items()}
        ind_reg_h = EmPrEP_Serie_Historica_mun.groupby(lambda x: map_reg_s.get(str(x), 'Ind')).sum().div(Vinculados_mun2.groupby(lambda x: map_reg_s.get(str(x), 'Ind')).sum()).fillna(0).round(2)
        df_mk_reg = viz.gerar_analise_regioes(pd.concat([ind_reg_h.reindex(ORDEM_REGIOES), df_mes_br]), args.output_dir)
        map_uf_s = {str(k): v for k, v in df_ibge.set_index('codigo_ibge_resid')[col_uf].to_dict().items()}
        ind_uf_h = EmPrEP_Serie_Historica_mun.groupby(lambda x: map_uf_s.get(str(x), 'Ind')).sum().div(Vinculados_mun2.groupby(lambda x: map_uf_s.get(str(x), 'Ind')).sum()).fillna(0).round(2)
        df_mk_uf = viz.gerar_analise_uf(ind_uf_h.sort_index(), args.output_dir, map_cod_sigla)
        df_mk_final = pd.concat([df_mk_reg, df_mk_uf], ignore_index=True)

    # 6c. SOCIODEMOGRÁFICO (RAÇA)
    print("\n--- ANÁLISE SOCIODEMOGRÁFICA (RAÇA) ---")
    df_p_h_raw, df_v_h_raw = gerar_series_mensais_raca(df_prep, df_disp, df_pvha, df_ibge, args.data_fechamento)
    df_raca_snap, df_raca_h_br, df_mk_raca_br = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    dict_series_reg, dict_mk_reg, dict_totais_reg = {}, {}, {}

    if not df_p_h_raw.empty:
        # Brasil
        p_br, v_br = df_p_h_raw.groupby(level='raca').sum(), df_v_h_raw.groupby(level='raca').sum()
        df_raca_h_br = p_br.div(v_br).fillna(0).round(2)
        df_mk_raca_br = socio.calcular_mann_kendall_raca(df_raca_h_br, 18)
        dict_series_reg['Brasil'], dict_mk_reg['Brasil'] = df_raca_h_br, df_mk_raca_br
        dict_totais_reg['Brasil'] = df_p_h_raw.sum().div(df_v_h_raw.sum()).fillna(0).round(2)
        
        # Regiões
        for r in df_p_h_raw.index.get_level_values(0).unique():
            if r == 'Ignorada': continue
            p_r, v_r = df_p_h_raw.xs(r, level=0), df_v_h_raw.xs(r, level=0)
            ind_r = p_r.div(v_r).fillna(0).round(2)
            dict_series_reg[r], dict_mk_reg[r] = ind_r, socio.calcular_mann_kendall_raca(ind_r, 18)
            dict_totais_reg[r] = p_r.sum().div(v_r.sum()).fillna(0).round(2)
        
        # Snapshot
        df_r_ativos = df_prep[df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente']
        df_v_novos = df_pvha[(df_pvha['Menor Data'] > start_6m) & (df_pvha['Menor Data'] <= dt_fechamento)]
        df_raca_snap = socio.calcular_indicador_raca(df_r_ativos, df_v_novos)
        
        socio.gerar_graficos_regionais_raca(dict_series_reg, args.output_dir, dict_mk_reg, dict_totais_reg)

    # SALVAR EXCEL
    fn = f"Indicador_PrEP_{mes:02d}_{ano}.xlsx"; path_ex = os.path.join(args.output_dir, fn)
    print(f"Salvando: {fn} ...")
    try:
        with pd.ExcelWriter(path_ex, engine='openpyxl') as wr:
            gerar_tabela_resumo(Indicador_UF_Unique['Grupo'], 'Qtd UF').to_excel(wr, sheet_name="Geral")
            Indicador[['regiao_Res','UF_Res','Sigla_UF','codigo_ibge_resid','Município','Populacao_resid','Vinculados','Em PrEP','Indicador_Mun','Grupo']].to_excel(wr, sheet_name="Município", index=False)
            Indicador_UF_Unique.to_excel(wr, sheet_name="UF", index=False); Indicador_Reg_Unique.to_excel(wr, sheet_name="Região", index=False)
            Indicador_Nac.to_excel(wr, sheet_name="Nacional"); Indicador_mes_mun.to_excel(wr, sheet_name="Mensal_municipio"); df_mes_br.to_excel(wr, sheet_name="Mensal_BR")
            if not df_mk_final.empty: df_mk_final.to_excel(wr, sheet_name="Mann_Kendall", index=False)
            if not df_raca_snap.empty:
                df_raca_snap.to_excel(wr, sheet_name="Raca_Cor", startrow=0)
                c_r = len(df_raca_snap) + 4
                wr.sheets['Raca_Cor'].cell(row=c_r, column=1, value="Série Histórica Mensal (Brasil)")
                df_raca_h_br.to_excel(wr, sheet_name="Raca_Cor", startrow=c_r)
                c_r += len(df_raca_h_br) + 4
                if not df_mk_raca_br.empty:
                    wr.sheets['Raca_Cor'].cell(row=c_r, column=1, value="Mann-Kendall (Brasil)")
                    df_mk_raca_br.to_excel(wr, sheet_name="Raca_Cor", startrow=c_r, index=False)
        print("Arquivo salvo com sucesso.")
        if os.path.exists(args.output_dir): shutil.copy2(fn, os.path.join(args.output_dir, fn))
    except Exception as e: print(f"Erro ao salvar: {e}")

    # =============================================================================
    # GERAR ARQUIVO AHA (Solicitação Específica)
    # =============================================================================
    print("\n--- GERANDO ARQUIVO AHA ---")
    
    pasta_aha = os.path.join(args.output_dir, "AHA")
    os.makedirs(pasta_aha, exist_ok=True)

    # Mapa Fixo de Capitais AHA
    mapa_aha = {
        'Campo Grande': '5002704',
        'Curitiba': '4106902',
        'Florianópolis': '4205407',
        'Fortaleza': '2304400',
        'Porto Alegre': '4314902'
    }
    
    rows_aha = []
    
    # Adicionar Capitais (Busca direta pelo ID no índice)
    for nome_cap, cod_ibge in mapa_aha.items():
        if cod_ibge in Indicador_mes_mun.index:
            row = Indicador_mes_mun.loc[cod_ibge].copy()
            # Remover nome_mun se estiver nas colunas para não duplicar
            if 'nome_mun' in row: del row['nome_mun']
            
            row['IBGE'] = cod_ibge
            row.name = nome_cap
            rows_aha.append(row)
            print(f"      OK: {nome_cap} (ID {cod_ibge})")
        else:
            print(f"      [ERRO] {nome_cap} (ID {cod_ibge}) não encontrado na base.")

    # Adicionar Brasil
    if not df_mes_br.empty:
        r_b = df_mes_br.iloc[0].copy()
        r_b['IBGE'] = '0'
        r_b.name = 'Brasil'
        rows_aha.append(r_b)
    
    # Criar DataFrame Final
    if rows_aha:
        df_aha = pd.DataFrame(rows_aha)
        
        # CHAMADA VISUALIZAÇÃO AHA (Antes de formatação final)
        # Passar dataframe limpo (sem IBGE) para os gráficos
        graf_aha = df_aha.drop(columns=['IBGE'], errors='ignore')
        df_mk_aha = viz.gerar_analise_aha(graf_aha, pasta_aha)
        
        # FORMATAÇÃO FINAL PARA EXCEL
        # Converter índice (Nomes) em coluna 'Município'
        df_aha.index.name = 'Município'
        df_aha.reset_index(inplace=True)
        
        # Reordenar colunas: IBGE na frente
        cols_dados = [c for c in df_aha.columns if c not in ['IBGE', 'Município']]
        df_aha = df_aha[['IBGE', 'Município'] + cols_dados]
        
        with pd.ExcelWriter(os.path.join(pasta_aha, f"Indicador_PrEP_AHA_{mes:02d}_{ano}.xlsx")) as wr:
            df_aha.to_excel(wr, sheet_name="Dados", index=False)
            if not df_mk_aha.empty:
                df_mk_aha.to_excel(wr, sheet_name="Mann_Kendall", index=False)
                
    else:
        print("   Erro: Nenhuma capital ou dados do Brasil para AHA.")

    viz.gerar_grafico_brasil(Indicador_mes_BR, args.output_dir)
    d = time.time() - start_time; print(f"\n--- CONCLUÍDO EM: {d/60:.2f} min ({d:.1f} s) ---")

if __name__ == "__main__": main()