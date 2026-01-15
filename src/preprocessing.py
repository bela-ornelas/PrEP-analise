import pandas as pd
import numpy as np
from .config import UF_MAP, REGIAO_MAP

def enrich_disp_data(df_disp_semdupl, df_cadastro, df_pvha, df_pvha_prim, df_ibge=None):
    """
     Enriquece o dataframe de dispensa com dados de cadastro, UF, Região, Óbito e IBGE.
    """
    if df_disp_semdupl.empty:
        return df_disp_semdupl

    print("Enriquecendo dados de Dispensa...")

    # 1. UF e Região da UDM
    # Disp['Cod_IBGE'] = Disp['cod_ibge_udm'].astype(str)
    # Disp['Cod_UF'] = Disp['Cod_IBGE'].str[:2]
    df_disp_semdupl['Cod_IBGE'] = df_disp_semdupl['cod_ibge_udm'].astype(str).str.split('.').str[0] # Handle float conversion
    df_disp_semdupl['Cod_UF'] = df_disp_semdupl['Cod_IBGE'].str[:2]
    
    df_disp_semdupl['UF_UDM'] = df_disp_semdupl['Cod_UF'].map(UF_MAP).fillna('Error')
    df_disp_semdupl['regiao_UDM'] = df_disp_semdupl['Cod_UF'].map(REGIAO_MAP).fillna('Error')
    
    # 2. Merge com IBGE Municipal (Nome do município)
    # Se df_ibge for passado (não implementamos carregamento yet, mas o notebook carrega Tabela_IBGE_UF...xlsx)
    # Vamos pular se não tiver df_ibge, assumindo que UF_UDM é mais critico para análise
    
    # 3. Merge com Cadastro
    if not df_cadastro.empty:
        # Padronizar nomes de colunas
        df_disp_semdupl.columns = df_disp_semdupl.columns.str.strip()
        df_cadastro.columns = df_cadastro.columns.str.strip()
        
        # Merge
        df_disp_semdupl = df_disp_semdupl.merge(
            df_cadastro[['codigo_paciente', 'Cod_unificado']],
            on='codigo_paciente',
            how='left'
        )
        df_disp_semdupl['Cod_unificado'] = df_disp_semdupl['Cod_unificado'].astype('Int64')

    # 4. Merge com PVHA (Óbito e Primeira Dispensa PVHA)
    if not df_pvha.empty:
          pvha_sel = df_pvha[['Cod_unificado', 'data_obito', 'PVHA']].copy() # Adicionei PVHA coluna pois notebook usa
          # Merge
          if 'Cod_unificado' in df_disp_semdupl.columns:
               df_disp_semdupl = df_disp_semdupl.merge(pvha_sel, on='Cod_unificado', how='left')
    
    if not df_pvha_prim.empty:
         prim_sel = df_pvha_prim[['Cod_unificado', 'data_min']].rename(columns={'data_min': 'data_min_PVHA'})
         if 'Cod_unificado' in df_disp_semdupl.columns:
              df_disp_semdupl = df_disp_semdupl.merge(prim_sel, on='Cod_unificado', how='left')

    # 5. Filtrar Óbitos
    # Disp_semdupl = Disp_semdupl[Disp_semdupl['data_obito'].isna()]
    if 'data_obito' in df_disp_semdupl.columns:
        original_len = len(df_disp_semdupl)
        df_disp_semdupl = df_disp_semdupl[df_disp_semdupl['data_obito'].isna()]
        print(f"Removidos {original_len - len(df_disp_semdupl)} registros de óbito.")

    return df_disp_semdupl

def calculate_intervals(df_disp_semdupl):
    # Lógica de intervalo de testes (Cell 35)
    # Disp_semdupl['dt_resultado_testagem_hiv'] = pd.to_datetime(...)
    # Disp_semdupl['dias_teste_disp'] = (Disp_semdupl['dt_disp'] - Disp_semdupl['dt_resultado_hiv']).dt.days
    
    if 'dt_resultado_testagem_hiv' in df_disp_semdupl.columns:
        df_disp_semdupl['dt_resultado_testagem_hiv'] = pd.to_datetime(df_disp_semdupl['dt_resultado_testagem_hiv'], errors='coerce')
        df_disp_semdupl['dt_resultado_hiv'] = df_disp_semdupl['dt_resultado_testagem_hiv'].dt.normalize()
        df_disp_semdupl['dias_teste_disp'] = (df_disp_semdupl['dt_disp'] - df_disp_semdupl['dt_resultado_hiv']).dt.days
    
    return df_disp_semdupl

def flag_first_last_disp(df_disp_semdupl):
    # Disp_semdupl['prim_disp'] = ...
    # Disp_semdupl['ult_disp'] = ...
    print("Calculando primeira e última dispensa...")
    df_disp_semdupl['prim_disp'] = (df_disp_semdupl['dt_disp'] == df_disp_semdupl.groupby('codigo_pac_eleito')['dt_disp'].transform('min')).astype(int)
    df_disp_semdupl['ult_disp'] = (df_disp_semdupl['dt_disp'] == df_disp_semdupl.groupby('codigo_pac_eleito')['dt_disp'].transform('max')).astype(int)
    return df_disp_semdupl
