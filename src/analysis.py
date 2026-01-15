import pandas as pd
from .config import MONTHS_ORDER

def generate_disp_metrics(df_disp_semdupl):
    """
    Gera métricas de dispensação por Mês/Ano.
    """
    if df_disp_semdupl.empty:
        return pd.DataFrame()

    print("Gerando métricas de Dispensas...")
    # Crosstabulation (Cell 38/39)
    # index=mes_disp, columns=ano_disp
    crosstab_result = pd.crosstab(index=df_disp_semdupl['mes_disp'], 
                                  columns=df_disp_semdupl['ano_disp'])
    
    # Reindex
    crosstab_result = crosstab_result.reindex(MONTHS_ORDER)
    
    # Add Total per column
    totals = crosstab_result.sum()
    crosstab_result.loc['Total'] = totals
    
    return crosstab_result

def generate_new_users_metrics(df_disp_semdupl):
    """
    Gera métricas de Novos Usuários por Mês/Ano.
    Considera novos usuários aqueles com 'prim_disp' == 1.
    """
    print("Gerando métricas de Novos Usuários...")
    # Filter for first dispensation
    if 'prim_disp' not in df_disp_semdupl.columns:
        return pd.DataFrame()
        
    df_first = df_disp_semdupl[df_disp_semdupl['prim_disp'] == 1].copy()
    
    # Ensure distinct users (one row per user)
    df_first = df_first.drop_duplicates(subset=['codigo_pac_eleito'])
    
    if df_first.empty:
        return pd.DataFrame()

    crosstab_result = pd.crosstab(index=df_first['mes_disp'], 
                                  columns=df_first['ano_disp'])
    
    crosstab_result = crosstab_result.reindex(MONTHS_ORDER)
    
    totals = crosstab_result.sum()
    crosstab_result.loc['Total'] = totals
    
    return crosstab_result

def classify_prep_users(df_disp_semdupl, data_fechamento):
    """
    Classifica usuários:
    - Disp_Ultimos_12m: Teve dispensa nos últimos 12 meses.
    - EmPrEP_Atual: Critério de adesão baseado em duracao * 1.4 >= data_fim
    """
    print("Classificando usuários (EmPrEP, Ultimos 12m)...")
    if df_disp_semdupl.empty:
        return {"Disp_Ultimos_12m": 0, "EmPrEP_Atual": 0}
        
    hoje_dt = pd.to_datetime(data_fechamento).normalize()
    
    # Garantir que dt_disp é datetime
    df_disp_semdupl['dt_disp'] = pd.to_datetime(df_disp_semdupl['dt_disp'])
    
    # Calcular valid_until
    if 'duracao_sum' not in df_disp_semdupl.columns:
         if 'duracao' in df_disp_semdupl.columns:
             df_disp_semdupl['duracao_sum'] = df_disp_semdupl['duracao']
         else:
             df_disp_semdupl['duracao_sum'] = 30 # Default
             
    df_disp_semdupl['valid_until'] = df_disp_semdupl['dt_disp'] + pd.to_timedelta(df_disp_semdupl['duracao_sum'] * 1.4, unit='D')
    
    start_date_12m = hoje_dt - pd.DateOffset(years=1)
    
    # Identificar a última dispensa de cada paciente para classificação
    df_latest = df_disp_semdupl.sort_values(by="dt_disp", ascending=False).drop_duplicates(['codigo_pac_eleito'], keep='first').copy()
    
    # Flags no dataframe original (última dispensa)
    df_latest['Disp_Ultimos_12m'] = ((df_latest['dt_disp'] > start_date_12m) & (df_latest['dt_disp'] <= hoje_dt)).astype(int)
    df_latest['EmPrEP_Atual'] = ((df_latest['Disp_Ultimos_12m'] == 1) & (df_latest['valid_until'] >= hoje_dt)).astype(int)
    
    # Merge de volta para o dataframe principal se necessário (ou apenas retornar as contagens)
    count_12m = df_latest['Disp_Ultimos_12m'].sum()
    count_emprep = df_latest['EmPrEP_Atual'].sum()
    
    total_pacientes_unicos = df_disp_semdupl['codigo_pac_eleito'].nunique()
    count_nao_12m = total_pacientes_unicos - count_12m
    count_descontinuados = count_12m - count_emprep
    
    # IMPORTANTE: Guardar o status no dataframe para uso em outras funções
    df_disp_semdupl['is_EmPrEP_Atual'] = df_disp_semdupl['codigo_pac_eleito'].isin(df_latest[df_latest['EmPrEP_Atual'] == 1]['codigo_pac_eleito'])
    
    return {
        "Disp_Ultimos_12m": count_12m,
        "Disp_Ultimos_12m_Nao": count_nao_12m,
        "EmPrEP_Atual": count_emprep,
        "Descontinuados": count_descontinuados
    }

def generate_population_metrics(df_disp_semdupl):
    """
    Gera tabela de populações (aba Populações (em PrEP))
    Filtra apenas quem está em PrEP atualmente.
    """
    print("Gerando métricas de Populações (apenas Em PrEP atualmente)...")
    
    # Filtro PrEP_current conforme solicitado
    if 'is_EmPrEP_Atual' not in df_disp_semdupl.columns:
        return pd.DataFrame()
        
    df_current = df_disp_semdupl[df_disp_semdupl['is_EmPrEP_Atual'] == True].copy()
    
    if df_current.empty:
        return pd.DataFrame()
        
    # Deduplicar por paciente para contar pessoas, não dispensas
    df_current_users = df_current.drop_duplicates(subset=['codigo_pac_eleito'])
    
    # Frequência de Pop_genero_pratica
    pop_counts = df_current_users['Pop_genero_pratica'].value_counts()
    pop_perc = (df_current_users['Pop_genero_pratica'].value_counts(normalize=True) * 100).round(2)
    
    pop_tab = pd.DataFrame({
        'Pop_genero_pratica': pop_counts.index,
        'Freq_Val': pop_counts.values,
        'Freq_Rel': pop_perc.values
    })
    
    # Ordenar conforme o notebook (decrescente por valor)
    pop_tab = pop_tab.sort_values(by='Freq_Val', ascending=False)
    
    return pop_tab

def generate_prep_history(df_disp_semdupl, data_fechamento):
    """
    Gera tabela histórica (2018 até Ano Atual) com:
    - Ano
    - Pelo menos uma dispensação nos últimos 12 meses
    - Em PrEP
    - % Em PrEP
    
    Lógica:
    Para anos anteriores: Referência é 31/12/ANO.
    Para ano atual: Referência é data_fechamento.
    """
    print("Gerando histórico de adesão (2018-Hoje)...")
    if df_disp_semdupl.empty:
        return pd.DataFrame()
        
    hoje_dt = pd.to_datetime(data_fechamento).normalize()
    ano_atual = hoje_dt.year
    anual_metrics = []
    
    # Pre-calculates valid_until globally as it depends only on row data, not reference date
    # Garantir datetime
    df_disp_semdupl['dt_disp'] = pd.to_datetime(df_disp_semdupl['dt_disp'])
    
    # Calcular valid_until
    if 'duracao_sum' not in df_disp_semdupl.columns:
         if 'duracao' in df_disp_semdupl.columns:
             df_disp_semdupl['duracao_sum'] = df_disp_semdupl['duracao']
         else:
             df_disp_semdupl['duracao_sum'] = 30 
             
    df_disp_semdupl['valid_until'] = df_disp_semdupl['dt_disp'] + pd.to_timedelta(df_disp_semdupl['duracao_sum'] * 1.4, unit='D')
    
    for year in range(2018, ano_atual + 1):
        if year == ano_atual:
            ref_date = hoje_dt
        else:
            ref_date = pd.Timestamp(year=year, month=12, day=31)
            
        start_date_12m = ref_date - pd.DateOffset(years=1)
        
        # 1. Disp_Ultimos_12m
        # Filter: dt_disp > start_date_12m AND dt_disp <= ref_date
        past_year_disp = df_disp_semdupl[
            (df_disp_semdupl['dt_disp'] > start_date_12m) & 
            (df_disp_semdupl['dt_disp'] <= ref_date)
        ].copy()
        
        users_12m = past_year_disp['codigo_pac_eleito'].nunique()
        
        # 2. Em PrEP
        # Filter: latest dispensation within 12m window must be valid until >= ref_date
        if past_year_disp.empty:
            users_emprep = 0
        else:
             past_year_disp = past_year_disp.sort_values(by="dt_disp", ascending=False)
             past_year_disp_deduplicated = past_year_disp.drop_duplicates(['codigo_pac_eleito'], keep='first')
             
             valid_dispensations = past_year_disp_deduplicated[
                past_year_disp_deduplicated['valid_until'] >= ref_date
             ]
             users_emprep = valid_dispensations['codigo_pac_eleito'].nunique()
        
        anual_metrics.append({
            'Ano': year,
            'Pelo menos uma dispensação nos últimos 12 meses': users_12m,
            'Em PrEP': users_emprep
        })
        
    df_history = pd.DataFrame(anual_metrics)
    
    if not df_history.empty:
        df_history['% Em PrEP'] = ((df_history['Em PrEP'] / df_history['Pelo menos uma dispensação nos últimos 12 meses']) * 100).round(1)
        
    return df_history
