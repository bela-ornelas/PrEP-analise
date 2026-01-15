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
    
    # Calcular valid_until como no notebook
    # Disp_semdupl['valid_until'] = Disp_semdupl['dt_disp'] + pd.to_timedelta(Disp_semdupl['duracao_sum'] * 1.4, unit='D')
    if 'duracao_sum' not in df_disp_semdupl.columns:
         if 'duracao' in df_disp_semdupl.columns:
             df_disp_semdupl['duracao_sum'] = df_disp_semdupl['duracao']
         else:
             df_disp_semdupl['duracao_sum'] = 30 # Default
             
    df_disp_semdupl['valid_until'] = df_disp_semdupl['dt_disp'] + pd.to_timedelta(df_disp_semdupl['duracao_sum'] * 1.4, unit='D')
    
    # Lógica iterativa simplificada para o mês atual (data de fechamento)
    # No notebook: loop for year/month... if year==ano and month==mes...
    
    start_date_12m = hoje_dt - pd.DateOffset(years=1)
    
    # 1. Disp_Ultimos_12m (Teve dispensa nos ultimos 12 meses)
    # Filter: dt_disp > start_date_12m AND dt_disp <= hoje_dt
    # No notebook: "past_year_dispensations"
    
    past_year_disp = df_disp_semdupl[
        (df_disp_semdupl['dt_disp'] > start_date_12m) & 
        (df_disp_semdupl['dt_disp'] <= hoje_dt)
    ].copy()
    
    # Deduplicar por paciente (o notebook faz drop_duplicates(['codigo_pac_eleito'], keep="first") após ordenar por data desc)
    past_year_disp = past_year_disp.sort_values(by="dt_disp", ascending=False)
    users_with_disp_12m = past_year_disp['codigo_pac_eleito'].unique() # List of users
    
    count_12m = len(users_with_disp_12m)
    
    # 2. EmPrEP_Atual
    # Notebook: valid_dispensations = past_year_dispensations[past_year_dispensations['valid_until'] >= end_date]
    # Aqui end_date é a data de fechamento (hoje_dt)
    
    # Importante: O notebook aplica o filtro de validade SOBRE o dataframe já filtrado dos últimos 12 meses e deduplicado (maior data)
    # Ou seja, pega a ÚLTIMA dispensa de cada paciente nos ultimos 12m e vê se ela cobre a data atual.
    
    # Vamos pegar 'past_year_disp' (que contém todas as dispensas do ano)
    # E deduplicar mantendo a mais recente para cada paciente
    past_year_disp_deduplicated = past_year_disp.drop_duplicates(['codigo_pac_eleito'], keep='first')
    
    valid_dispensations = past_year_disp_deduplicated[
        past_year_disp_deduplicated['valid_until'] >= hoje_dt
    ]
    
    count_emprep = valid_dispensations['codigo_pac_eleito'].nunique()
    
    # Gerar arquivo TXT com labels exatos pedidos
    # "Teve dispensação nos últimos 12 meses"
    # "Não teve dispensação nos últimos 12 meses" -> Total de pacientes únicos na base inteira - count_12m?
    # O notebook faz um merge left com a base total para preencher "Não teve..."
    
    total_pacientes_unicos = df_disp_semdupl['codigo_pac_eleito'].nunique()
    count_nao_12m = total_pacientes_unicos - count_12m
    
    count_descontinuados = count_12m - count_emprep
    
    return {
        "Disp_Ultimos_12m": count_12m,
        "Disp_Ultimos_12m_Nao": count_nao_12m,
        "EmPrEP_Atual": count_emprep,
        "Descontinuados": count_descontinuados
    }

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
