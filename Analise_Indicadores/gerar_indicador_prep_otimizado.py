import pandas as pd
import numpy as np
import sys
import os
import argparse
from datetime import datetime
import shutil
from pathlib import Path

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

# Mapeamento Fixo IBGE -> Sigla (Garantia para nomes de arquivos)
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
    
    # 1. PrEP Único
    print(f"   Carregando PrEP Único: {args.path_prep}")
    if not os.path.exists(args.path_prep): raise FileNotFoundError(f"Arquivo não encontrado: {args.path_prep}")
    df_prep = pd.read_parquet(args.path_prep)
    # Ajuste tipos
    for col in ['codigo_ibge_resid', 'cod_ibge_udm']:
        if col in df_prep.columns:
            df_prep[col] = pd.to_numeric(df_prep[col], errors='coerce')

    # 2. PrEP Dispensas (Necessário para histórico mensal)
    print(f"   Carregando PrEP Dispensas: {args.path_disp}")
    if not os.path.exists(args.path_disp): raise FileNotFoundError(f"Arquivo não encontrado: {args.path_disp}")
    df_disp = pd.read_parquet(args.path_disp)
    
    # 3. PVHA
    print(f"   Carregando PVHA: {args.path_pvha}")
    if not os.path.exists(args.path_pvha): raise FileNotFoundError(f"Arquivo não encontrado: {args.path_pvha}")
    df_pvha = pd.read_parquet(args.path_pvha)
    if "Menor Data" not in df_pvha.columns and "data_min" in df_pvha.columns:
        df_pvha["Menor Data"] = pd.to_datetime(df_pvha["data_min"], errors="coerce")
    
    # Extrair População
    pop_ibge = pd.DataFrame()
    if 'Populacao_resid' in df_pvha.columns and 'codigo_ibge_resid' in df_pvha.columns:
        pop_ibge = (
            df_pvha[['Populacao_resid', 'codigo_ibge_resid']]
            .drop_duplicates(subset='codigo_ibge_resid')
            .dropna(subset=['codigo_ibge_resid'])
            .copy()
        )
        pop_ibge['Populacao_resid'] = pd.to_numeric(pop_ibge['Populacao_resid'], errors='coerce').fillna(0).astype(int)
        pop_ibge['codigo_ibge_resid'] = pd.to_numeric(pop_ibge['codigo_ibge_resid'], errors='coerce').fillna(0).astype(int).astype(str)

    # 4. IBGE
    print(f"   Carregando Tabela IBGE: {args.path_ibge}")
    df_ibge = pd.DataFrame()
    if os.path.exists(args.path_ibge):
        df_ibge = pd.read_excel(args.path_ibge)
        df_ibge["codigo_ibge_resid"] = df_ibge["codigo_ibge_resid"].astype(str).str.replace('.0', '', regex=False)

    return df_prep, df_disp, df_pvha, df_ibge, pop_ibge

# =============================================================================
# CÁLCULO DE SÉRIES HISTÓRICAS (MENSAL)
# =============================================================================

def gerar_series_mensais(df_prep, df_disp, df_pvha, data_fechamento):
    """
    Gera DataFrames com histórico mensal de EmPrEP e Vinculados por município.
    Range: Jan/2018 até Data Fechamento.
    """
    print("\n--- GERANDO SÉRIES MENSAIS (MUNICÍPIO) ---")
    
    start_date = pd.to_datetime("2022-01-01")
    end_date = pd.to_datetime(data_fechamento)
    dates = pd.date_range(start=start_date, end=end_date, freq='ME') # Month End
    
    # --- 1. SÉRIE Em PrEP ---
    # Preparar Dispensas
    # Merge com PrEP para pegar município de residência atualizado/correto
    cols_merge = ['codigo_pac_eleito', 'codigo_ibge_resid', 'cod_ibge_udm']
    df_merge = df_disp.merge(df_prep[cols_merge], on='codigo_pac_eleito', how='left', suffixes=('_disp', ''))
    
    # Definir município (Residência > UDM)
    df_merge['mun_final'] = df_merge['codigo_ibge_resid'].fillna(df_merge['cod_ibge_udm'])
    df_merge['mun_final'] = pd.to_numeric(df_merge['mun_final'], errors='coerce').fillna(0).astype(int).astype(str)
    df_merge = df_merge[df_merge['mun_final'] != '0']

    # Calcular validade da dispensa
    # Se 'duracao_sum' ou 'duracao' não existir, assume 30. Se existir, usa.
    col_duracao = 'duracao_sum' if 'duracao_sum' in df_merge.columns else 'duracao'
    if col_duracao not in df_merge.columns:
        df_merge['duracao_val'] = 30
    else:
        df_merge['duracao_val'] = pd.to_numeric(df_merge[col_duracao], errors='coerce').fillna(30)
    
    df_merge['dt_disp'] = pd.to_datetime(df_merge['dt_disp'], errors='coerce')
    # Regra: Data Dispensa + Duração * 1.4 (Grace period)
    df_merge['valid_until'] = df_merge['dt_disp'] + pd.to_timedelta(df_merge['duracao_val'] * 1.4, unit='D')
    
    # Otimização: Vetores numpy para loop rápido
    arr_pac = df_merge['codigo_pac_eleito'].values
    arr_mun = df_merge['mun_final'].values
    arr_disp = df_merge['dt_disp'].values.astype('datetime64[D]')
    arr_valid = df_merge['valid_until'].values.astype('datetime64[D]')
    
    prep_results = []
    
    # --- 2. SÉRIE Vinculados ---
    # Preparar PVHA
    df_pvha_clean = df_pvha.dropna(subset=['Menor Data', 'codigo_ibge_resid']).copy()
    df_pvha_clean['codigo_ibge_resid'] = pd.to_numeric(df_pvha_clean['codigo_ibge_resid'], errors='coerce').fillna(0).astype(int).astype(str)
    df_pvha_clean = df_pvha_clean[df_pvha_clean['codigo_ibge_resid'] != '0']
    
    arr_pvha_mun = df_pvha_clean['codigo_ibge_resid'].values
    arr_pvha_data = df_pvha_clean['Menor Data'].values.astype('datetime64[D]')
    
    vinc_results = []
    
    print(f"   Calculando mês a mês ({len(dates)} meses)...")
    
    for date_ref in dates:
        col_name = f"{date_ref.month}_{date_ref.year}"
        date_ref_np = date_ref.to_datetime64()
        
        # A) Em PrEP
        # Filtro: Dispensa válida na data de referência E dispensa feita até a data
        # Nota: Retirada a janela de 2 anos para alinhar estritamente com a validade calculada (logica original)
        mask_prep = (arr_valid >= date_ref_np) & (arr_disp <= date_ref_np)
        
        if np.any(mask_prep):
            # Usuários ativos neste mês
            # Drop duplicates para garantir 1 usuário por município
            temp_df = pd.DataFrame({'pac': arr_pac[mask_prep], 'mun': arr_mun[mask_prep]})
            # Se o usuário mudou de município, pega o mais recente (aqui simplificado, pega qualquer um válido no range, ou último da base)
            # Como arr_mun vem do merge com PrEP_unico (cadastro atual), o município é constante para o paciente histórico. 
            # Se quiséssemos histórico real de mudança, teríamos que usar o mun da dispensa. 
            # O snippet original usa PrEP_historico_mun que vem de (Disp join Cad). Então usa mun do cadastro atual.
            counts_prep = temp_df.drop_duplicates(subset='pac')['mun'].value_counts()
            counts_prep.name = col_name
            prep_results.append(counts_prep)
        else:
            prep_results.append(pd.Series(name=col_name, dtype=int))
            
        # B) Vinculados
        start_6m_np = (date_ref - pd.DateOffset(months=6)).to_datetime64()
        mask_vinc = (arr_pvha_data > start_6m_np) & (arr_pvha_data <= date_ref_np)
        
        if np.any(mask_vinc):
            counts_vinc = pd.DataFrame({'mun': arr_pvha_mun[mask_vinc]})['mun'].value_counts()
            counts_vinc.name = col_name
            vinc_results.append(counts_vinc)
        else:
            vinc_results.append(pd.Series(name=col_name, dtype=int))

    # Consolidar DataFrames
    EmPrEP_Serie_Historica_mun = pd.concat(prep_results, axis=1).fillna(0).astype(int)
    Vinculados_mun2 = pd.concat(vinc_results, axis=1).fillna(0).astype(int)
    
    return EmPrEP_Serie_Historica_mun, Vinculados_mun2

# =============================================================================
# CÁLCULO ATUAL (OTIMIZADO)
# =============================================================================

def calcular_atual(df_prep, df_pvha, data_fechamento):
    """Cálculos do indicador atual (Numerador e Denominador)."""
    print("\n--- CALCULANDO INDICADOR ATUAL ---")
    
    # Numerador (Em PrEP Atual)
    if 'EmPrEP_Atual' not in df_prep.columns:
        raise ValueError("Coluna 'EmPrEP_Atual' não encontrada em PrEP_unico.")
        
    df_ativos = df_prep[df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente'].copy()
    df_ativos['mun_final'] = df_ativos['codigo_ibge_resid'].fillna(df_ativos['cod_ibge_udm'])
    df_ativos['mun_final'] = pd.to_numeric(df_ativos['mun_final'], errors='coerce').fillna(0).astype(int).astype(str)
    df_ativos = df_ativos[df_ativos['mun_final'] != '0']
    numerador = df_ativos['mun_final'].value_counts()
    
    # Denominador (Novos Vinculados 6m)
    hoje = pd.to_datetime(data_fechamento)
    start_6m = hoje - pd.DateOffset(months=6)
    mask = (df_pvha['Menor Data'] > start_6m) & (df_pvha['Menor Data'] <= hoje)
    df_novos = df_pvha[mask].copy()
    df_novos['codigo_ibge_resid'] = pd.to_numeric(df_novos['codigo_ibge_resid'], errors='coerce').fillna(0).astype(int).astype(str)
    df_novos = df_novos[df_novos['codigo_ibge_resid'] != '0']
    denominador = df_novos['codigo_ibge_resid'].value_counts()
    
    return numerador, denominador

# =============================================================================
# AUXILIARES DE CLASSIFICAÇÃO
# =============================================================================

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
    contagem = series_grupo.value_counts()
    ordem = ["Sem novos vinculados e sem PrEP", 'Sem novos vinculados, com pessoas em PrEP', 
             "Grupo 0", "Grupo 1", "Grupo 2", "Grupo 3", "Grupo 4"]
    porcentagem = (contagem / contagem.sum()) * 100
    df = pd.DataFrame({nome_col_qtd: contagem, '%': porcentagem.round(1)})
    df = df.reindex(ordem).fillna(0)
    df[nome_col_qtd] = df[nome_col_qtd].astype(int)
    total = df[nome_col_qtd].sum()
    linha_total = pd.DataFrame({nome_col_qtd: [total], '%': [100]}, index=['Total'])
    return pd.concat([df, linha_total])

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_fechamento", required=True)
    parser.add_argument("--path_prep", default=PATH_PREP_UNICO)
    parser.add_argument("--path_disp", default=PATH_PREP_DISP)
    parser.add_argument("--path_pvha", default=PATH_PVHA)
    parser.add_argument("--path_ibge", default=PATH_IBGE)
    parser.add_argument("--output_dir", default=OUTPUT_DIR)
    args = parser.parse_args()
    
    print(f"=== GERADOR INDICADOR PrEP:HIV (OTIMIZADO) ===")
    print(f"Data Fechamento: {args.data_fechamento}")
    
    dt_fechamento = pd.to_datetime(args.data_fechamento)
    mes, ano = dt_fechamento.month, dt_fechamento.year
    
    # 1. Load
    df_prep, df_disp, df_pvha, df_ibge, pop_ibge = load_data(args)
    
    # 2. Atual
    num_atual, den_atual = calcular_atual(df_prep, df_pvha, args.data_fechamento)
    
    # 3. Séries Mensais (Para aba Mensal_municipio)
    EmPrEP_Serie_Historica_mun, Vinculados_mun2 = gerar_series_mensais(df_prep, df_disp, df_pvha, args.data_fechamento)
    
    # 4. Consolidar Indicador Atual (Geral)
    print("\n--- CONSOLIDANDO INDICADOR ATUAL ---")
    all_muns = pd.Index(num_atual.index).union(pd.Index(den_atual.index))
    
    # Mapa IBGE
    if not df_ibge.empty:
        all_muns = pd.Index(df_ibge['codigo_ibge_resid'].unique())
        map_ibge = df_ibge.set_index('codigo_ibge_resid')
    else:
        map_ibge = pd.DataFrame()
        
    Indicador = pd.DataFrame(index=all_muns)
    Indicador.index.name = 'codigo_ibge_resid'
    Indicador['Em PrEP'] = num_atual.reindex(all_muns).fillna(0).astype(int)
    Indicador['Vinculados'] = den_atual.reindex(all_muns).fillna(0).astype(int)
    
    # Enriquecer Geográfico
    if not map_ibge.empty:
        # Detecção de colunas mais robusta
        cols_lower = {c.lower(): c for c in map_ibge.columns}
        
        # UF: Tenta encontrar 'uf', 'sigla_uf', etc
        col_uf = next((c for c in map_ibge.columns if c.lower() in ['uf', 'sigla_uf', 'sg_uf']), None)
        if not col_uf: col_uf = next((c for c in map_ibge.columns if 'uf' in c.lower()), 'UF')
        
        # Tentar identificar explicitamente a Sigla se col_uf for Código
        # Geralmente tabela IBGE tem 'codigo_uf' e 'sigla_uf' ou 'uf' (sigla) e 'nome_uf'
        col_sigla_uf = next((c for c in map_ibge.columns if c.lower() in ['sigla_uf', 'sg_uf', 'uf_sigla']), None)
        # Se não achou sigla explícita, verifica se a col_uf já parece ser sigla (texto curto) ou código
        # Mas vamos assumir o que foi detectado em col_uf como primário.
            
        # Região: Tenta encontrar 'regiao', 'nome_regiao'
        col_reg = next((c for c in map_ibge.columns if 'regia' in c.lower()), 'Região')
        
        # Município: Evitar colunas que tenham 'uf' no nome (ex: Nome_UF)
        candidatos_mun = [c for c in map_ibge.columns if ('nome' in c.lower() or 'municip' in c.lower()) and 'uf' not in c.lower()]
        # Preferência por 'nome_mun' ou 'municipio'
        col_nome = next((c for c in candidatos_mun if c.lower() in ['nome_mun', 'municipio', 'no_municipio']), None)
        if not col_nome:
             col_nome = candidatos_mun[0] if candidatos_mun else 'nome_mun'
             
        print(f"   Colunas detectadas no IBGE -> Mun: '{col_nome}', UF: '{col_uf}', Reg: '{col_reg}'")

        Indicador['Município'] = Indicador.index.map(map_ibge[col_nome]).fillna('Desconhecido')
        Indicador['UF_Res'] = Indicador.index.map(map_ibge[col_uf]).fillna('Ign')
        Indicador['regiao_Res'] = Indicador.index.map(map_ibge[col_reg]).fillna('Ign')
        
        # Criar mapa Código UF -> Sigla UF para nomes de arquivos
        # Inicializa com o mapa fixo de garantia
        map_cod_sigla = MAP_UF_SIGLA.copy()
        
        if col_sigla_uf:
             temp_map = map_ibge[[col_uf, col_sigla_uf]].drop_duplicates().set_index(col_uf)[col_sigla_uf].to_dict()
             map_cod_sigla.update({str(k): v for k, v in temp_map.items()})
             # Adiciona Sigla ao dataframe principal para conferência
             Indicador['Sigla_UF'] = Indicador.index.map(map_ibge[col_sigla_uf]).fillna(Indicador['UF_Res'].astype(str).map(MAP_UF_SIGLA)).fillna(Indicador['UF_Res'])
        else:
             # Usa o mapa fixo para preencher a coluna Sigla_UF
             Indicador['Sigla_UF'] = Indicador['UF_Res'].astype(str).map(MAP_UF_SIGLA).fillna(Indicador['UF_Res'])
             
    else:
        Indicador[['Município', 'UF_Res', 'regiao_Res', 'Sigla_UF']] = 'Desconhecido'
        map_cod_sigla = MAP_UF_SIGLA.copy()

    # Enriquecer População
    if not pop_ibge.empty:
        Indicador = Indicador.merge(pop_ibge, on='codigo_ibge_resid', how='left').fillna({'Populacao_resid': 0})
    else:
        Indicador['Populacao_resid'] = 0

    # Cálculos Indicador
    Indicador['Indicador_Mun'] = Indicador.apply(lambda x: round(x['Em PrEP']/x['Vinculados'], 2) if x['Vinculados'] > 0 else 0, axis=1)
    Indicador['Grupo'] = Indicador.apply(classificar_grupo_mun, axis=1)
    
    # Agregados UF
    Indicador['Vinculados_UF'] = Indicador.groupby(["UF_Res"])['Vinculados'].transform('sum')
    Indicador['Em PrEP_UF'] = Indicador.groupby(["UF_Res"])['Em PrEP'].transform('sum')
    Indicador["Indicador_UF"] = (Indicador["Em PrEP_UF"]/Indicador["Vinculados_UF"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    
    # Agregados Região
    Indicador['Vinculados_Reg'] = Indicador.groupby(["regiao_Res"])['Vinculados'].transform('sum')
    Indicador['Em PrEP_Reg'] = Indicador.groupby(["regiao_Res"])['Em PrEP'].transform('sum')
    Indicador["Indicador_Reg"] = (Indicador["Em PrEP_Reg"]/Indicador["Vinculados_Reg"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    
    # 5. Processar Aba Mensal_municipio (Lógica do Usuário)
    print("--- PROCESSANDO ABA MENSAL_MUNICIPIO ---")
    
    # Garantir strings no índice
    EmPrEP_Serie_Historica_mun.index = EmPrEP_Serie_Historica_mun.index.astype(str)
    Vinculados_mun2.index = Vinculados_mun2.index.astype(str)
    
    # Mapa cod -> nome
    if not df_ibge.empty:
        # Reutilizando a lógica robusta de detecção
        candidatos_mun = [c for c in df_ibge.columns if ('nome' in c.lower() or 'municip' in c.lower()) and 'uf' not in c.lower()]
        col_nome_ibge = next((c for c in candidatos_mun if c.lower() in ['nome_mun', 'municipio', 'no_municipio']), None)
        if not col_nome_ibge: col_nome_ibge = candidatos_mun[0] if candidatos_mun else 'nome_mun'
        
        map_mun = df_ibge[["codigo_ibge_resid", col_nome_ibge]].drop_duplicates("codigo_ibge_resid").set_index("codigo_ibge_resid")[col_nome_ibge]
        codigos_ibge = df_ibge["codigo_ibge_resid"].sort_values().unique()
    else:
        # Fallback
        map_mun = Indicador['Município']
        codigos_ibge = Indicador.index.unique()
    
    # Reindexar
    prep_hist = EmPrEP_Serie_Historica_mun.reindex(codigos_ibge)
    vinc_hist = Vinculados_mun2.reindex(codigos_ibge)
    
    # Calcular
    base_calc = prep_hist.div(vinc_hist)
    base_calc = base_calc.replace([np.inf, -np.inf], np.nan)
    Indicador_mes_mun = base_calc.fillna(0).round(2)
    
    # Inserir nome
    Indicador_mes_mun.insert(0, "nome_mun", map_mun.reindex(Indicador_mes_mun.index))
    
    # Ordenar colunas meses
    cols_meses = [c for c in Indicador_mes_mun.columns if c != "nome_mun"]
    cols_meses_ordenadas = sorted(cols_meses, key=lambda x: (int(x.split("_")[1]), int(x.split("_")[0])))
    Indicador_mes_mun = Indicador_mes_mun[["nome_mun"] + cols_meses_ordenadas]

    # 6. Tabelas Finais e Ordenação de Região
    Indicador_UF_Unique = Indicador.drop_duplicates("UF_Res")[["UF_Res","Vinculados_UF","Em PrEP_UF","Indicador_UF"]].copy()
    Indicador_UF_Unique['Grupo'] = Indicador_UF_Unique.apply(classificar_grupo_uf, axis=1)
    Indicador_UF_Unique = Indicador_UF_Unique.sort_values('UF_Res')

    Indicador_Reg_Unique = Indicador.drop_duplicates("regiao_Res")[["regiao_Res","Vinculados_Reg","Em PrEP_Reg","Indicador_Reg"]].copy()
    # Aplicar Ordem Região
    Indicador_Reg_Unique['regiao_Res'] = pd.Categorical(Indicador_Reg_Unique['regiao_Res'], categories=ORDEM_REGIOES, ordered=True)
    Indicador_Reg_Unique = Indicador_Reg_Unique.sort_values("regiao_Res")
    
    Indicador_Nac = pd.DataFrame({
        "Vinculados": [Indicador['Vinculados'].sum()],
        "Em PrEP": [Indicador['Em PrEP'].sum()],
        "Indicador_Nac": [(Indicador['Em PrEP'].sum() / Indicador['Vinculados'].sum()) if Indicador['Vinculados'].sum() > 0 else 0]
    }, index=["Brasil"]).round(2)

    # Tabelas Resumo
    tabela_geral_UF = gerar_tabela_resumo(Indicador_UF_Unique['Grupo'], 'Qtd UF')
    tabela_geral_mun = gerar_tabela_resumo(Indicador['Grupo'], 'Qtd municípios')
    tabela_mun_50k = gerar_tabela_resumo(Indicador[Indicador['Populacao_resid'] >= 50000]['Grupo'], 'Qtd municípios >=50.000 hab')

    # CONFERÊNCIA
    print("\n" + "="*50)
    print("CONFERÊNCIA DE DADOS (BRASIL)")
    print("="*50)
    print(f"   Vinculados: {Indicador_Nac['Vinculados'].values[0]}")
    print(f"   Em PrEP:    {Indicador_Nac['Em PrEP'].values[0]}")
    print(f"   Indicador:  {Indicador_Nac['Indicador_Nac'].values[0]}")
    print("="*50 + "\n")

    # SALVAR
    filename = f"Indicador_PrEP_{mes:02d}_{ano}.xlsx"
    if not os.path.exists(args.output_dir): os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Salvando: {filename} ...")
    cols_mun = ['regiao_Res', 'UF_Res', 'Sigla_UF', 'codigo_ibge_resid','Município','Populacao_resid','Vinculados', 'Em PrEP','Indicador_Mun','Grupo']
    
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            tabela_geral_UF.to_excel(writer, sheet_name="Geral")
            tabela_geral_mun.to_excel(writer, sheet_name="Geral", startrow=len(tabela_geral_UF) + 3)
            tabela_mun_50k.to_excel(writer, sheet_name="Geral", startrow=len(tabela_geral_UF) + 3 + len(tabela_geral_mun) + 3)
            
            # Garantir colunas existentes
            cols_to_save = [c for c in cols_mun if c in Indicador.columns]
            
            Indicador[cols_to_save].to_excel(writer, sheet_name="Município", index=False)
            Indicador[Indicador["Populacao_resid"] >= 50000][cols_to_save].to_excel(writer, sheet_name="Município_50k", index=False)
            Indicador_UF_Unique.to_excel(writer, sheet_name="UF", index=False)
            Indicador_Reg_Unique.to_excel(writer, sheet_name="Região", index=False)
            Indicador_Nac.to_excel(writer, sheet_name="Nacional")
            Indicador_mes_mun.to_excel(writer, sheet_name="Mensal_municipio")
            
        print(f"Arquivo salvo com sucesso.")
        if os.path.exists(args.output_dir):
            shutil.copy2(filename, os.path.join(args.output_dir, filename))
            print(f"Cópia na rede: {os.path.join(args.output_dir, filename)}")
            
    except Exception as e:
        print(f"Erro ao salvar: {e}")

    # =============================================================================
    # GERAR ARQUIVOS POR UF
    # =============================================================================
    print("\n--- GERANDO ARQUIVOS INDIVIDUAIS POR UF ---")
    pasta_saida_uf = r"V:\2026\Monitoramento e Avaliação\DOCUMENTOS\PrEP\Indicador PrEP HIV\Indicador UF"
    
    if not os.path.exists(pasta_saida_uf):
        try:
            os.makedirs(pasta_saida_uf, exist_ok=True)
        except:
            print(f"Aviso: Não foi possível criar/acessar diretório de UF: {pasta_saida_uf}")
            # Fallback para local se rede falhar
            pasta_saida_uf = os.path.join(args.output_dir, "Indicador UF")
            os.makedirs(pasta_saida_uf, exist_ok=True)

    ufs = Indicador['UF_Res'].unique()
    
    # Diagnóstico de totais para conferência
    print("   [Diagnóstico] Verificando totais antes da quebra por UF:")
    # Exemplo MG (31)
    mg_code = next((u for u in ufs if str(u) == '31'), None)
    if mg_code:
        check_mg = Indicador[Indicador['UF_Res'] == mg_code]
        print(f"      MG (Code 31) -> Linhas: {len(check_mg)}, Vinculados: {check_mg['Vinculados'].sum()}, Em PrEP: {check_mg['Em PrEP'].sum()}")
    
    for uf in ufs:
        if str(uf) in ['Ign', 'nan', 'None', 'Desconhecido']: continue
        
        # Determinar Nome/Sigla para o arquivo
        # Tenta pegar da coluna Sigla_UF na primeira ocorrência desse UF
        try:
            sigla_row = Indicador[Indicador['UF_Res'] == uf]['Sigla_UF'].iloc[0]
            sigla = str(sigla_row).strip().upper()
        except:
            sigla = str(uf).strip().upper()
        
        # Se a sigla ainda for numérica (ex: "31"), e tivermos o mapa, tenta usar
        if sigla.isdigit() and map_cod_sigla:
             sigla = str(map_cod_sigla.get(str(uf), sigla))

        aba1 = Indicador_UF_Unique[Indicador_UF_Unique['UF_Res'] == uf]
        
        # Aba 2: Municípios > 50k
        cols_to_save_uf = [c for c in cols_mun if c in Indicador.columns]
        aba2 = Indicador[
            (Indicador['UF_Res'] == uf) &
            (Indicador["Populacao_resid"] >= 50000)
        ][cols_to_save_uf]
        
        nome_arquivo = f"Indicador_PrEP_{sigla}_{mes}_{ano}.xlsx"
        caminho_arquivo = os.path.join(pasta_saida_uf, nome_arquivo)
        
        try:
            with pd.ExcelWriter(caminho_arquivo, engine='openpyxl') as writer:
                aba1.to_excel(writer, sheet_name="Indicador_UF", index=False)
                aba2.to_excel(writer, sheet_name="Municípios_50000+", index=False)
            print(f"   Salvo: {nome_arquivo} (UF: {uf})")
        except Exception as e:
            print(f"   Erro ao salvar {nome_arquivo}: {e}")

    # =============================================================================
    # GERAR ARQUIVO AHA (Solicitação Específica)
    # =============================================================================
    print("\n--- GERANDO ARQUIVO AHA ---")
    
    # Definir pasta de saída
    pasta_aha = os.path.join(r"V:\2026\Monitoramento e Avaliação\DOCUMENTOS\PrEP\Indicador PrEP HIV", "AHA")
    if not os.path.exists(pasta_aha):
        try:
            os.makedirs(pasta_aha, exist_ok=True)
        except:
             # Fallback para output_dir local/rede definido nos argumentos
             pasta_aha = os.path.join(args.output_dir, "AHA")
             os.makedirs(pasta_aha, exist_ok=True)

    # 1. Calcular Série Histórica Brasil
    # Soma de todos os municípios mês a mês
    prep_brasil_hist = EmPrEP_Serie_Historica_mun.sum()
    vinc_brasil_hist = Vinculados_mun2.sum()
    
    # Calcular indicador Brasil
    ind_brasil_hist = prep_brasil_hist.div(vinc_brasil_hist).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
    
    # 2. Identificar Códigos das Capitais Escolhidas
    # Lista de interesse
    cap_nomes = ['Campo Grande', 'Curitiba', 'Florianópolis', 'Fortaleza', 'Porto Alegre']
    
    # Mapa auxiliar Nome -> UF para desambiguação (ex: Campo Grande MS vs AL)
    cap_uf_map = {
        'Campo Grande': 'MS',
        'Curitiba': 'PR',
        'Florianópolis': 'SC',
        'Fortaleza': 'CE',
        'Porto Alegre': 'RS'
    }
    
    # Lista final de DataFrames para concatenar
    rows_aha = []
    
    # Adicionar Capitais
    for nome in cap_nomes:
        uf_alvo = cap_uf_map.get(nome)
        
        # Tentar encontrar o código IBGE correto no DataFrame 'Indicador'
        # Verifica se Sigla_UF existe, senão tenta UF_Res
        if 'Sigla_UF' in Indicador.columns:
            mask = (Indicador['Município'].str.lower() == nome.lower()) & (Indicador['Sigla_UF'].astype(str).str.upper() == uf_alvo)
        else:
            # Fallback se Sigla_UF não foi gerada corretamente (tenta usar o mapa fixo no UF_Res)
            # Assume que UF_Res pode ser código, então converte
            mask = (Indicador['Município'].str.lower() == nome.lower()) & (Indicador['UF_Res'].astype(str).map(MAP_UF_SIGLA).fillna(Indicador['UF_Res']).str.upper() == uf_alvo)
            
        match = Indicador[mask]
        
        if not match.empty:
            cod_ibge = match.index[0] # Pega o primeiro match (código ibge)
            
            # Buscar a série histórica deste código em Indicador_mes_mun
            # Indicador_mes_mun tem 'nome_mun' e as colunas de data. O index é o código IBGE (definido na linha 343)
            if cod_ibge in Indicador_mes_mun.index:
                # Selecionar linha, remover 'nome_mun' e renomear series para o Nome da Capital
                row = Indicador_mes_mun.loc[cod_ibge].drop('nome_mun', errors='ignore')
                row.name = nome
                rows_aha.append(row)
        else:
            print(f"   Aviso: Capital não encontrada na base: {nome} ({uf_alvo})")

    # Adicionar Brasil
    ind_brasil_hist.name = 'Brasil'
    
    # Garantir que as colunas do Brasil estejam na mesma ordem/set das capitais
    # Pegar as colunas de meses do Indicador_mes_mun (que já foram ordenadas na linha 353)
    cols_meses_finais = [c for c in Indicador_mes_mun.columns if c != 'nome_mun']
    rows_aha.append(ind_brasil_hist[cols_meses_finais])
    
    # Criar DataFrame Final
    if rows_aha:
        df_aha = pd.DataFrame(rows_aha)
        
        # Reordenar linhas conforme a lista solicitada + Brasil
        ordem_final = cap_nomes + ['Brasil']
        df_aha = df_aha.reindex(ordem_final)
        
        # Salvar
        filename_aha = f"Indicador_PrEP_AHA_{mes:02d}_{ano}.xlsx"
        path_arquivo_aha = os.path.join(pasta_aha, filename_aha)
        
        try:
            df_aha.to_excel(path_arquivo_aha)
            print(f"   Arquivo AHA salvo com sucesso: {path_arquivo_aha}")
        except Exception as e:
            print(f"   Erro ao salvar arquivo AHA: {e}")
    else:
        print("   Erro: Nenhuma capital ou dados do Brasil foram processados para o arquivo AHA.")

if __name__ == "__main__":
    main()