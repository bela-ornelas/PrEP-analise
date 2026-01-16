import pandas as pd
import numpy as np

def create_prep_dataframe(df_disp_semdupl, df_cad_prep, df_cad_hiv=pd.DataFrame(), df_pvha=pd.DataFrame(), df_pvha_prim=pd.DataFrame()):
    """
    Cria o dataframe consolidado 'df PrEP' (uma linha por paciente),
    juntando dados do Cadastro com a última dispensa e métricas históricas.
    """
    print("Gerando DataFrame consolidado 'df PrEP'...")
    
    if df_cad_prep.empty:
        return pd.DataFrame()

    # Garantir datetime no Disp
    if not df_disp_semdupl.empty and 'dt_disp' in df_disp_semdupl.columns:
        df_disp_semdupl['dt_disp'] = pd.to_datetime(df_disp_semdupl['dt_disp'])
        df_disp_semdupl['ano_disp'] = df_disp_semdupl['dt_disp'].dt.year

    # 1. Calcular Métricas Históricas por Paciente
    if not df_disp_semdupl.empty:
        grp = df_disp_semdupl.groupby('codigo_pac_eleito')
        agg_df = grp.agg(
            dt_disp_min=('dt_disp', 'min'),
            dt_disp_max=('dt_disp', 'max'),
            duracao_sum_total=('duracao_sum', 'sum')
        ).reset_index()
        
        # Datas Min/Max por Ano
        grp_ano = df_disp_semdupl.groupby(['codigo_pac_eleito', 'ano_disp']).agg(
            min_date=('dt_disp', 'min'),
            max_date=('dt_disp', 'max')
        ).reset_index()
        
        pivot_min = grp_ano.pivot(index='codigo_pac_eleito', columns='ano_disp', values='min_date')
        pivot_max = grp_ano.pivot(index='codigo_pac_eleito', columns='ano_disp', values='max_date')
        
        pivot_min.columns = [f'dt_disp_min_{col}' for col in pivot_min.columns]
        pivot_max.columns = [f'dt_disp_max_{col}' for col in pivot_max.columns]
        
        agg_df = agg_df.merge(pivot_min, on='codigo_pac_eleito', how='left')
        agg_df = agg_df.merge(pivot_max, on='codigo_pac_eleito', how='left')
        
        # 2. Obter a Última Dispensa
        df_last_disp = df_disp_semdupl.sort_values(by=['codigo_pac_eleito', 'dt_disp'], ascending=[True, False])
        df_last_disp = df_last_disp.drop_duplicates(subset=['codigo_pac_eleito'], keep='first')
    else:
        df_last_disp = pd.DataFrame()
        agg_df = pd.DataFrame()
    
    # 3. Merge Base: Cadastro + Última Dispensa
    df_prep = df_cad_prep.copy()
    
    if not df_last_disp.empty:
        df_prep = df_prep.merge(df_last_disp, on='codigo_pac_eleito', how='left', suffixes=('', '_disp'))
        df_prep = df_prep.merge(agg_df, on='codigo_pac_eleito', how='left')
    
    # -------------------------------------------------------------------------
    # MERGES ADICIONAIS (Solicitados)
    # -------------------------------------------------------------------------
    
    # A) Cadastro HIV (Trazer Cod_unificado) - Chave: codigo_paciente
    if not df_cad_hiv.empty and 'codigo_paciente' in df_prep.columns:
        print("Merge Adicional 1: Cadastro HIV (Cod_unificado)...")
        cad_hiv_sel = df_cad_hiv[['codigo_paciente', 'Cod_unificado']].drop_duplicates(subset=['codigo_paciente'])
        
        # Se Cod_unificado já existir (vindo do Dispensa), vamos priorizar o do Cadastro HIV ou manter o que tem?
        # Normalmente o merge sobrescreve ou cria sufixo. Vamos assumir que queremos preencher/atualizar.
        if 'Cod_unificado' in df_prep.columns:
            df_prep = df_prep.drop(columns=['Cod_unificado']) # Remove para trazer limpo do Cad HIV
            
        df_prep = df_prep.merge(cad_hiv_sel, on='codigo_paciente', how='left')
        df_prep['Cod_unificado'] = df_prep['Cod_unificado'].astype('Int64')

    # B) PVHA Prim (Trazer data_min_PVHA) - Chave: Cod_unificado
    if not df_pvha_prim.empty and 'Cod_unificado' in df_prep.columns:
        print("Merge Adicional 2: PVHA Prim (Data Diagnóstico)...")
        pvha_prim_sel = df_pvha_prim[['Cod_unificado', 'data_min']].rename(columns={'data_min': 'data_min_PVHA'})
        pvha_prim_sel = pvha_prim_sel.drop_duplicates(subset=['Cod_unificado'])
        
        df_prep = df_prep.merge(pvha_prim_sel, on='Cod_unificado', how='left')

    # C) PVHA (Trazer data_obito, PVHA) - Chave: Cod_unificado
    if not df_pvha.empty and 'Cod_unificado' in df_prep.columns:
        print("Merge Adicional 3: PVHA (Óbito/Status)...")
        pvha_sel = df_pvha[['Cod_unificado', 'data_obito', 'PVHA']].copy()
        pvha_sel = pvha_sel.drop_duplicates(subset=['Cod_unificado'])
        
        # Remover colunas se já existirem para evitar duplicidade (x, y)
        cols_to_drop = [c for c in ['data_obito', 'PVHA'] if c in df_prep.columns]
        if cols_to_drop:
            df_prep = df_prep.drop(columns=cols_to_drop)
            
        df_prep = df_prep.merge(pvha_sel, on='Cod_unificado', how='left')

    # 4. Calcular/Garantir Variáveis Derivadas Finais
    if 'dt_disp_min' in df_prep.columns:
        df_prep['ano_pri_disp'] = pd.to_datetime(df_prep['dt_disp_min']).dt.year
        df_prep['mes_pri_disp'] = pd.to_datetime(df_prep['dt_disp_min']).dt.month_name().str[:3]
    
    if 'dt_disp_max' in df_prep.columns:
        df_prep['ano_ult_disp'] = pd.to_datetime(df_prep['dt_disp_max']).dt.year
        df_prep['mes_ult_disp'] = pd.to_datetime(df_prep['dt_disp_max']).dt.month_name().str[:3]
    
    return df_prep
