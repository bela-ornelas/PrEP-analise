import pandas as pd
import numpy as np
from .config import MONTHS_ORDER

def generate_disp_metrics(df_disp_semdupl):
    """
    Gera métricas de dispensação por Mês/Ano.
    """
    if df_disp_semdupl.empty:
        return pd.DataFrame()

    print("Gerando métricas de Dispensas...")
    # Crosstabulation
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
    Retorna um dicionário com contagens rápidas para o relatório geral.
    Baseia-se nas colunas 'Disp_Ultimos_12m' e 'EmPrEP_Atual' já calculadas.
    """
    print("Calculando totais para resumo (Geral)...")
    
    if df_disp_semdupl.empty:
        return {"Disp_Ultimos_12m": 0, "Disp_Ultimos_12m_Nao": 0, "EmPrEP_Atual": 0, "Descontinuados": 0}
        
    # Como as flags já foram geradas em generate_prep_history, basta contar
    # Mas precisamos contar por PACIENTE ÚNICO
    df_unique = df_disp_semdupl.drop_duplicates(subset=['codigo_pac_eleito'])
    
    count_12m = len(df_unique[df_unique['Disp_Ultimos_12m'] == 'Teve dispensação nos últimos 12 meses'])
    count_emprep = len(df_unique[df_unique['EmPrEP_Atual'] == 'Em PrEP atualmente'])
    
    total_pacientes = len(df_unique)
    count_nao_12m = total_pacientes - count_12m
    count_descontinuados = count_12m - count_emprep
    
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
    
    if 'EmPrEP_Atual' not in df_disp_semdupl.columns or 'Pop_genero_pratica' not in df_disp_semdupl.columns:
        return pd.DataFrame()
        
    # Filtra apenas quem está Em PrEP atualmente
    df_current = df_disp_semdupl[df_disp_semdupl['EmPrEP_Atual'] == 'Em PrEP atualmente'].copy()
    
    if df_current.empty:
        return pd.DataFrame()
        
    # Deduplicar por paciente para contar pessoas
    df_current_users = df_current.drop_duplicates(subset=['codigo_pac_eleito'])
    
    # Frequência de Pop_genero_pratica
    pop_counts = df_current_users['Pop_genero_pratica'].value_counts()
    pop_perc = (df_current_users['Pop_genero_pratica'].value_counts(normalize=True) * 100).round(2)
    
    pop_tab = pd.DataFrame({
        'Pop_genero_pratica': pop_counts.index,
        'Freq_Val': pop_counts.values,
        'Freq_Rel': pop_perc.values
    })
    
    pop_tab = pop_tab.sort_values(by='Freq_Val', ascending=False)
    
    return pop_tab

def generate_prep_history(df_disp_semdupl, data_fechamento):
    """
    Gera histórico mensal detalhado de adesão (Em PrEP vs Descontinuados) e enriquece
    o dataframe com flags anuais conforme lógica do usuário.
    """
    print("Gerando histórico detalhado mensal (2018-Hoje)...")
    
    hoje_dt = pd.to_datetime(data_fechamento).normalize()
    ano_atual = hoje_dt.year
    mes_atual = hoje_dt.month
    
    # Garantir datetime
    df_disp_semdupl['dt_disp'] = pd.to_datetime(df_disp_semdupl['dt_disp'])
    
    # Calcular valid_until
    if 'duracao_sum' not in df_disp_semdupl.columns:
         if 'duracao' in df_disp_semdupl.columns:
             df_disp_semdupl['duracao_sum'] = df_disp_semdupl['duracao']
         else:
             df_disp_semdupl['duracao_sum'] = 30
             
    df_disp_semdupl['valid_until'] = df_disp_semdupl['dt_disp'] + pd.to_timedelta(df_disp_semdupl['duracao_sum'] * 1.4, unit='D')
    
    EmPrEP_monthly_sample = pd.DataFrame(columns=['Year', 'Month', 'Em PrEP', 'Descontinuados'])
    
    # Loop mensal de Jan/2018 até a data de fechamento
    for year in range(2018, ano_atual + 1):
        for month in range(1, 13):
            # Parar se passar da data de fechamento
            if year == ano_atual and month > mes_atual:
                break

            last_day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
            start_date = last_day - pd.offsets.DateOffset(years=1)
            end_date = last_day
            
            # Filtro 12 meses
            past_year_disp = df_disp_semdupl[
                (df_disp_semdupl['dt_disp'] > start_date) & 
                (df_disp_semdupl['dt_disp'] <= end_date)
            ].copy()
            
            # Deduplicar mantendo a mais recente
            past_year_disp = past_year_disp.sort_values(by="dt_disp", ascending=False)
            past_year_disp = past_year_disp.drop_duplicates(['codigo_pac_eleito'], keep="first")
            
            # Validar adesão
            valid_disp = past_year_disp[past_year_disp['valid_until'] >= end_date].copy()
            
            # Lógica de salvamento de flags no DataFrame principal
            # Se for o mês exato do fechamento (data atual)
            if year == ano_atual and month == mes_atual:
                # Flags Atuais
                df_disp_semdupl.loc[df_disp_semdupl['codigo_pac_eleito'].isin(past_year_disp['codigo_pac_eleito']), "Disp_Ultimos_12m"] = 'Teve dispensação nos últimos 12 meses'
                df_disp_semdupl.loc[df_disp_semdupl['codigo_pac_eleito'].isin(valid_disp['codigo_pac_eleito']), "EmPrEP_Atual"] = "Em PrEP atualmente"
                
                # Flags do Ano Atual
                df_disp_semdupl.loc[df_disp_semdupl['codigo_pac_eleito'].isin(past_year_disp['codigo_pac_eleito']), f"Disp_12m_{year}"] = f'Teve dispensação em {year}'
                df_disp_semdupl.loc[df_disp_semdupl['codigo_pac_eleito'].isin(valid_disp['codigo_pac_eleito']), f"EmPrEP_{year}"] = f"Em PrEP {year}"
            
            # Se for Dezembro, salva flags do ano fechado
            elif month == 12:
                df_disp_semdupl.loc[df_disp_semdupl['codigo_pac_eleito'].isin(past_year_disp['codigo_pac_eleito']), f"Disp_12m_{year}"] = f'Teve dispensação em {year}'
                df_disp_semdupl.loc[df_disp_semdupl['codigo_pac_eleito'].isin(valid_disp['codigo_pac_eleito']), f"EmPrEP_{year}"] = f"Em PrEP {year}"

            # Contagens
            num_users_on_PrEP = valid_disp['codigo_pac_eleito'].nunique()
            num_discontinued = past_year_disp.shape[0] - num_users_on_PrEP
            
            new_row = pd.DataFrame({'Year': [year], 'Month': [month], 'Em PrEP': [num_users_on_PrEP], 'Descontinuados': [num_discontinued]})
            EmPrEP_monthly_sample = pd.concat([EmPrEP_monthly_sample, new_row], ignore_index=True)

    # -------------------------------------------------------------------------
    # AJUSTE FINAL DE FLAGS (Lógica do Usuário)
    # -------------------------------------------------------------------------
    
    # Preencher nulos iniciais
    if "EmPrEP_Atual" not in df_disp_semdupl.columns: df_disp_semdupl["EmPrEP_Atual"] = None
    if "Disp_Ultimos_12m" not in df_disp_semdupl.columns: df_disp_semdupl["Disp_Ultimos_12m"] = None

    # Ajusta a coluna Em PrEP Atual
    cond_atual = [
        df_disp_semdupl["EmPrEP_Atual"] == "Em PrEP atualmente",
        (df_disp_semdupl["Disp_Ultimos_12m"] == "Teve dispensação nos últimos 12 meses") & (df_disp_semdupl["EmPrEP_Atual"].isna())
    ]
    choices_atual = ["Em PrEP atualmente", "Estão descontinuados"]
    df_disp_semdupl["EmPrEP_Atual"] = np.select(cond_atual, choices_atual, default=None)

    # Ajusta flags anuais (retroativo)
    for ano_e in range(ano_atual, 2017, -1):
        col_emprep = f"EmPrEP_{ano_e}"
        col_disp12m = f"Disp_12m_{ano_e}"
        
        # Garantir existência das colunas
        if col_emprep not in df_disp_semdupl.columns: df_disp_semdupl[col_emprep] = None
        if col_disp12m not in df_disp_semdupl.columns: df_disp_semdupl[col_disp12m] = None
        
        cond_ano = [
            df_disp_semdupl[col_emprep] == f"Em PrEP {ano_e}",
            (df_disp_semdupl[col_disp12m] == f"Teve dispensação em {ano_e}") & (df_disp_semdupl[col_emprep].isna())
        ]
        choices_ano = [f"Em PrEP {ano_e}", f"Descontinuou em {ano_e}"]
        
        df_disp_semdupl[col_emprep] = np.select(cond_ano, choices_ano, default=None)

    return df_disp_semdupl, EmPrEP_monthly_sample

def classify_udm_active(df_disp_semdupl, data_fechamento):
    """
    Classifica se a UDM está ativa nos últimos 12 meses.
    """
    print("Classificando UDMs ativas...")
    hoje_dt = pd.to_datetime(data_fechamento).normalize()
    inicio_12m = hoje_dt - pd.DateOffset(years=1)
    
    udms_com_disp_12m = df_disp_semdupl.loc[
        (df_disp_semdupl['dt_disp'] > inicio_12m) & (df_disp_semdupl['dt_disp'] <= hoje_dt),
        'codigo_udm'
    ].unique()
    
    df_disp_semdupl['udm_ativa_12m'] = df_disp_semdupl['codigo_udm'].isin(udms_com_disp_12m)
    df_disp_semdupl['udm_ativa_12m'] = df_disp_semdupl['udm_ativa_12m'].map({True: 'UDM ativa', False: 'UDM não ativa'})
    
    return df_disp_semdupl