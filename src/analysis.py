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

def generate_new_users_metrics(df_prep):
    """
    Gera métricas de Novos Usuários por Mês/Ano.
    Baseado no df_prep consolidado (data da primeira dispensa).
    """
    print("Gerando métricas de Novos Usuários (Base Consolidada)...")
    
    # 1. Filtro: Apenas quem tem dispensa (dt_disp not null)
    # Nota: No consolidation, criamos 'dt_disp_min' que é a base para 'ano_pri_disp'.
    # Vamos checar se 'ano_pri_disp' existe.
    
    if df_prep.empty:
        return pd.DataFrame()
        
    if 'ano_pri_disp' not in df_prep.columns or 'mes_pri_disp' not in df_prep.columns:
        print("Aviso: Colunas de primeira dispensa não encontradas.")
        return pd.DataFrame()
    
    # Filtrar dados válidos
    # O notebook filtra: PrEP['dt_disp'].notnull(). No consolidation, dt_disp vem da última dispensa.
    # Mas se tem 'ano_pri_disp', é porque teve alguma dispensa.
    filtered_data = df_prep[df_prep['dt_disp'].notnull()].copy()

    # 2. Crosstab
    crosstab_result = pd.crosstab(index=filtered_data['mes_pri_disp'], 
                                  columns=filtered_data['ano_pri_disp'], 
                                  margins=False)
    
    # 3. Ordenação (Meses em Inglês -> Português)
    # O Pandas .dt.month_name() retorna em Inglês por padrão
    months_order_en = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    crosstab_result = crosstab_result.reindex(months_order_en)
    
    month_name_mapping = {
        'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr', 'May': 'Mai', 'Jun': 'Jun',
        'Jul': 'Jul', 'Aug': 'Ago', 'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
    }
    
    crosstab_result.index = crosstab_result.index.map(month_name_mapping)
    
    # 4. Total Row
    totals = crosstab_result.sum()
    crosstab_result.loc['Total'] = totals
    
    return crosstab_result

def classify_prep_users(df_prep, data_fechamento):
    """
    Retorna um dicionário com contagens rápidas para o relatório geral.
    Baseia-se no dataframe consolidado (df_prep).
    """
    print("Calculando totais para resumo (Geral) via df_prep...")
    
    if df_prep.empty:
        return {"Disp_Ultimos_12m": 0, "Disp_Ultimos_12m_Nao": 0, "EmPrEP_Atual": 0, "Descontinuados": 0}
        
    count_12m = len(df_prep[df_prep['Disp_Ultimos_12m'] == 'Teve dispensação nos últimos 12 meses'])
    count_emprep = len(df_prep[df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente'])
    
    total_pacientes = len(df_prep)
    iniciaram_prep = df_prep['dt_disp_min'].notnull().sum()
    count_nao_12m = total_pacientes - count_12m
    count_descontinuados = count_12m - count_emprep
    
    return {
        "Procuraram_PrEP": total_pacientes,
        "Iniciaram_PrEP": iniciaram_prep,
        "Disp_Ultimos_12m": count_12m,
        "Disp_Ultimos_12m_Nao": count_nao_12m,
        "EmPrEP_Atual": count_emprep,
        "Descontinuados": count_descontinuados
    }

def generate_population_metrics(df_prep):
    """
    Gera tabelas de frequência para variáveis sociodemográficas 
    (Pop_genero_pratica, fetar, escol4, raca4_cat)
    apenas para usuários 'Em PrEP atualmente'.
    """
    print("Gerando métricas de Populações (Em PrEP Atualmente)...")
    
    if df_prep.empty or 'EmPrEP_Atual' not in df_prep.columns:
        return pd.DataFrame()
        
    # Filtra apenas quem está Em PrEP atualmente
    df_current = df_prep[df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente'].copy()
    
    if df_current.empty:
        return pd.DataFrame()
    
    # Lista de variáveis para analisar
    # Ordem de exibição desejada
    variables = [
        ('Pop_genero_pratica', 'População Chave'),
        ('fetar', 'Faixa Etária'),
        ('escol4', 'Escolaridade'),
        ('raca4_cat', 'Raça/Cor')
    ]
    
    # Ordens Personalizadas
    order_fetar = ['<18', '18 a 24', '25 a 29', '30 a 39', '40 a 49', '50 e mais']
    order_escol = ['Sem educação formal a 3 anos', 'De 4 a 7 anos', 'De 8 a 11 anos', '12 ou mais anos', 'Ignorada/Não informada']
    
    dfs_to_concat = []
    
    for col, title in variables:
        if col not in df_current.columns:
            print(f"Aviso: Coluna '{col}' não encontrada em df_prep para relatório de população.")
            continue
            
        # Calcula frequência absoluta
        counts = df_current[col].value_counts(dropna=False)
        
        # Calcula frequência relativa (%)
        percs = df_current[col].value_counts(normalize=True, dropna=False) * 100
        
        # Montar DataFrame temporário
        temp_df = pd.DataFrame({
            'Categoria': counts.index, 
            'Frequência': counts.values,
            '%': percs.values.round(1)
        })
        
        # [CORREÇÃO] Converter para objeto para evitar erro de Categorical ao inserir texto novo
        temp_df['Categoria'] = temp_df['Categoria'].astype(object)
        
        # Tratamento de Nulos na Categoria para exibição
        temp_df['Categoria'] = temp_df['Categoria'].fillna('Ignorada/Não informada')
        
        # ORDENAÇÃO
        if col == 'fetar':
            # Aplicar ordem fixa
            temp_df['Categoria'] = pd.Categorical(temp_df['Categoria'], categories=order_fetar, ordered=True)
            temp_df = temp_df.sort_values('Categoria')
            
        elif col == 'escol4':
            # Aplicar ordem fixa
            # Garantir que 'Ignorada/Não informada' esteja presente ou tratada
            temp_df['Categoria'] = pd.Categorical(temp_df['Categoria'], categories=order_escol, ordered=True)
            temp_df = temp_df.sort_values('Categoria')
            
        else:
            # Ordenar por Frequência (Decrescente)
            temp_df = temp_df.sort_values(by='Frequência', ascending=False)
        
        # Adicionar Total da Seção
        total_count = temp_df['Frequência'].sum()
        total_perc = temp_df['%'].sum()
        
        total_row = pd.DataFrame({
            'Categoria': ['Total'],
            'Frequência': [total_count],
            '%': [round(total_perc, 1)]
        })
        
        # Adicionar Cabeçalho
        header_row = pd.DataFrame({'Categoria': [f"--- {title} ---"], 'Frequência': [None], '%': [None]})
        
        dfs_to_concat.append(header_row)
        dfs_to_concat.append(temp_df)
        dfs_to_concat.append(total_row)
        
        # Espaço
        empty_row = pd.DataFrame({'Categoria': [""], 'Frequência': [None], '%': [None]})
        dfs_to_concat.append(empty_row)

    if not dfs_to_concat:
        return pd.DataFrame()
        
    final_df = pd.concat(dfs_to_concat, ignore_index=True)
    return final_df

def generate_uf_summary(df_prep, df_disp_semdupl):
    """
    Gera tabela de dados por UF (Aba 'Dados por UF').
    Combina contagens de pacientes (df_prep) com total de dispensas (df_disp_semdupl).
    """
    print("Gerando resumo por UF (Aba 'Dados por UF')...")
    
    # 1. Agrupar df_prep (Pacientes)
    grouped_prep = df_prep.groupby(['regiao_UDM', 'UF_UDM', 'Cod_UF'])
    
    # Contagens específicas
    dispensation_count = grouped_prep['Disp_Ultimos_12m'].apply(lambda x: (x == 'Teve dispensação nos últimos 12 meses').sum())
    em_prep_count = grouped_prep['EmPrEP_Atual'].apply(lambda x: (x == 'Em PrEP atualmente').sum())
    descontinuados_count = grouped_prep['EmPrEP_Atual'].apply(lambda x: (x == 'Estão descontinuados').sum())
    
    UF_tab = pd.concat([dispensation_count, em_prep_count, descontinuados_count], axis=1)
    UF_tab.columns = ['dispensation_count', 'em_prep_count', 'descontinuados_count']
    
    # Porcentagem
    UF_tab['percentage'] = (UF_tab['em_prep_count'] / UF_tab['dispensation_count'] * 100).round(0)
    UF_tab = UF_tab.reset_index()
    
    # 2. Agrupar df_disp_semdupl (Total de Dispensas)
    # Nota: Aqui contamos LINHAS (cada dispensa única dt/pac), não pessoas únicas.
    disp_total = df_disp_semdupl.groupby('UF_UDM').size().reset_index()
    disp_total.columns = ['UF_UDM', 'disp_total']
    
    # 3. Merge e Formatação Final
    UF_tab = pd.merge(UF_tab, disp_total, on='UF_UDM', how='left')
    
    # Reordenar e Ordenar por Cod_UF
    UF_tab = UF_tab[['Cod_UF', 'regiao_UDM', 'UF_UDM', 'disp_total', 'dispensation_count', 'em_prep_count', 'descontinuados_count', 'percentage']].sort_values('Cod_UF')
    
    # Renomear
    UF_tab = UF_tab.rename(columns={
        'Cod_UF': 'Codigo UF',
        'regiao_UDM': 'Região',
        'UF_UDM': 'UF',
        'disp_total': 'Total de dispensas',
        'dispensation_count': 'Pelo menos uma dispensa nos últimos 12 meses',
        'em_prep_count': 'Estão em PrEP',
        'descontinuados_count': 'Descontinuados',
        'percentage': '% em PrEP'
    })
    
    return UF_tab

def generate_mun_summary(df_prep, df_disp_semdupl):
    """
    Gera tabela detalhada por Município/Serviço (Aba 'Mun').
    """
    print("Gerando resumo por Município/Serviço (Aba 'Mun')...")
    
    # Colunas de agrupamento
    group_cols = ['regiao_UDM', 'UF_UDM', 'Cod_UF', 'cod_ibge_udm', 'nome_mun_udm', 'nome_udm', 'endereco_udm', 'bairro_udm', 'cep_udm']
    
    # Verificar colunas existentes
    available_cols = [c for c in group_cols if c in df_prep.columns]
    
    if not available_cols:
        return pd.DataFrame()
    
    # 1. Agrupar df_prep
    grouped_prep = df_prep.groupby(available_cols)
    
    # Contagens
    dispensation_count = grouped_prep['Disp_Ultimos_12m'].apply(lambda x: (x == 'Teve dispensação nos últimos 12 meses').sum())
    em_prep_count = grouped_prep['EmPrEP_Atual'].apply(lambda x: (x == 'Em PrEP atualmente').sum())
    descontinuados_count = grouped_prep['EmPrEP_Atual'].apply(lambda x: (x == 'Estão descontinuados').sum())
    
    UF_mun_tab = pd.concat([dispensation_count, em_prep_count, descontinuados_count], axis=1)
    UF_mun_tab.columns = ['dispensation_count', 'em_prep_count', 'descontinuados_count']
    
    # Porcentagem
    UF_mun_tab['percentage'] = (UF_mun_tab['em_prep_count'] / UF_mun_tab['dispensation_count'] * 100).round(1)
    UF_mun_tab = UF_mun_tab.reset_index()
    
    # 2. Agrupar df_disp_semdupl (Total de Dispensas por Serviço)
    if 'nome_udm' in df_disp_semdupl.columns:
        disp_total = df_disp_semdupl.groupby('nome_udm').size().reset_index()
        disp_total.columns = ['nome_udm', 'disp_total']
        
        # Merge
        UF_mun_tab = pd.merge(UF_mun_tab, disp_total, on='nome_udm', how='left')
    else:
        UF_mun_tab['disp_total'] = 0
    
    # Reordenar colunas
    final_cols = available_cols + ['disp_total', 'dispensation_count', 'em_prep_count', 'descontinuados_count', 'percentage']
    
    # Sort
    if 'cod_ibge_udm' in UF_mun_tab.columns:
        UF_mun_tab = UF_mun_tab.sort_values('cod_ibge_udm')
        
    UF_mun_tab = UF_mun_tab[final_cols]
    
    # Renomear
    rename_map = {
        'Cod_UF': 'Codigo UF',
        'regiao_UDM': 'Região',
        'UF_UDM': 'UF',
        'cod_ibge_udm': 'Código IBGE',
        'nome_mun_udm': 'Município',
        'nome_udm': 'Nome do serviço',
        'endereco_udm': 'Endereço',
        'bairro_udm': 'Bairro',
        'cep_udm': 'CEP',
        'disp_total': 'Total de dispensas',
        'dispensation_count': 'Pelo menos uma dispensa nos últimos 12 meses',
        'em_prep_count': 'Estão em PrEP',
        'descontinuados_count': 'Descontinuados',
        'percentage': '% em PrEP'
    }
    
    UF_mun_tab = UF_mun_tab.rename(columns=rename_map)
    
    return UF_mun_tab

def generate_prep_history(df_disp_semdupl, data_fechamento):
    """
    Versão OTIMIZADA de generate_prep_history.
    Usa numpy arrays e reduz overhead de pandas.
    """
    print("Gerando histórico detalhado mensal (OTIMIZADO)...")
    
    hoje_dt = pd.to_datetime(data_fechamento).normalize()
    ano_atual = hoje_dt.year
    mes_atual = hoje_dt.month
    
    # 1. Preparação (Vetorizada)
    df_disp_semdupl['dt_disp'] = pd.to_datetime(df_disp_semdupl['dt_disp'])
    
    # Calcular valid_until (Vetorizado)
    if 'duracao_sum' not in df_disp_semdupl.columns:
         if 'duracao' in df_disp_semdupl.columns:
             df_disp_semdupl['duracao_sum'] = df_disp_semdupl['duracao']
         else:
             df_disp_semdupl['duracao_sum'] = 30
    
    # Trabalharemos com views locais para evitar warning de SettingWithCopy e acelerar
    # Criamos cópia leve apenas das colunas necessárias
    df_work = df_disp_semdupl[['codigo_pac_eleito', 'dt_disp', 'duracao_sum']].copy()
    df_work['valid_until'] = df_work['dt_disp'] + pd.to_timedelta(df_work['duracao_sum'] * 1.4, unit='D')
    
    # Salvar valid_until de volta no original pois é output esperado
    df_disp_semdupl['valid_until'] = df_work['valid_until']

    # Arrays Numpy para loop rápido
    arr_ids = df_work['codigo_pac_eleito'].values
    arr_dts = df_work['dt_disp'].values
    arr_valid = df_work['valid_until'].values
    
    history_rows = []
    
    # Datas de interesse para flags (Dezembros + Atual)
    dates_for_flags = {}
    for y in range(2018, ano_atual + 1): # Inclui ano atual
        dates_for_flags[(y, 12)] = f"{y}"
    # Sobrescreve/Adiciona a data atual exata se for requerida (se não for Dezembro já pega, se for Dezembro atualiza para Atual)
    # A logica original trata: se year==ano_atual e month==mes_atual -> Flags Atuais.
    dates_for_flags[(ano_atual, mes_atual)] = "Atual"
    
    # Loop Mensal (Jan 2018 -> Hoje)
    current_date = pd.Timestamp(2018, 1, 1) + pd.offsets.MonthEnd(0)
    
    while current_date <= hoje_dt:
        year = current_date.year
        month = current_date.month
        
        # Parar se passar da data de fechamento (mesmo ano, mês maior)
        if year == ano_atual and month > mes_atual:
            break

        # Intervalo de análise (Últimos 12 meses)
        end_date_np = current_date.to_datetime64()
        start_date_np = (current_date - pd.DateOffset(years=1)).to_datetime64()
        
        # MASK 1: Dispensas no intervalo (1 ano atrás < dt <= data_corte)
        mask_window = (arr_dts > start_date_np) & (arr_dts <= end_date_np)
        
        if not np.any(mask_window):
            history_rows.append({'Year': year, 'Month': month, 'Em PrEP': 0, 'Descontinuados': 0})
            # Avançar mês
            current_date = (current_date + pd.DateOffset(days=1)) + pd.offsets.MonthEnd(0)
            continue
            
        # Filtrar dados do intervalo
        ids_window = arr_ids[mask_window]
        dts_window = arr_dts[mask_window]
        valid_window = arr_valid[mask_window]
        
        # Deduplicar: Manter a dispensa mais recente por paciente
        # Usamos DataFrame temporário pois drop_duplicates é muito eficiente
        df_temp = pd.DataFrame({'id': ids_window, 'dt': dts_window, 'valid': valid_window})
        
        # Ordenar por data desc (para manter a first -> mais recente)
        # Note: arr_dts contém datas. Se df_temp['dt'] já for datetime, sort é rápido.
        df_temp = df_temp.sort_values('dt', ascending=False)
        df_unique = df_temp.drop_duplicates('id', keep='first')
        
        # Validar adesão (valid_until >= data_corte)
        mask_active = df_unique['valid'].values >= end_date_np
        
        active_ids = df_unique.loc[mask_active, 'id'].values
        all_window_ids = df_unique['id'].values
        
        num_users_on_PrEP = len(active_ids)
        num_discontinued = len(all_window_ids) - num_users_on_PrEP
        
        history_rows.append({'Year': year, 'Month': month, 'Em PrEP': num_users_on_PrEP, 'Descontinuados': num_discontinued})
        
        # ---------------------------------------------------------
        # Aplicar Flags no DataFrame Principal (Apenas datas chave)
        # ---------------------------------------------------------
        # Lógica original:
        # Se (year == ano_atual e month == mes_atual): Atual
        # Elif (month == 12): Ano Fechado
        
        is_current_target = (year == ano_atual and month == mes_atual)
        is_december = (month == 12)
        
        if is_current_target or is_december:
            # Definir sufixos e valores
            updates = []
            if is_current_target:
                updates.append(("Disp_Ultimos_12m", "EmPrEP_Atual", 'Teve dispensação nos últimos 12 meses', "Em PrEP atualmente"))
            
            if is_december:
                updates.append((f"Disp_12m_{year}", f"EmPrEP_{year}", f'Teve dispensação em {year}', f"Em PrEP {year}"))
            
            for col_disp, col_emprep, val_disp, val_emprep in updates:
                # Criar colunas se necessário
                if col_disp not in df_disp_semdupl.columns: df_disp_semdupl[col_disp] = None
                if col_emprep not in df_disp_semdupl.columns: df_disp_semdupl[col_emprep] = None
                
                # Atribuir valores
                # Usamos .loc com isin. É a forma segura.
                mask_all_main = df_disp_semdupl['codigo_pac_eleito'].isin(all_window_ids)
                mask_active_main = df_disp_semdupl['codigo_pac_eleito'].isin(active_ids)
                
                df_disp_semdupl.loc[mask_all_main, col_disp] = val_disp
                df_disp_semdupl.loc[mask_active_main, col_emprep] = val_emprep

        # Avançar mês
        current_date = (current_date + pd.DateOffset(days=1)) + pd.offsets.MonthEnd(0)

    EmPrEP_monthly_sample = pd.DataFrame(history_rows)

    # -------------------------------------------------------------------------
    # AJUSTE FINAL DE FLAGS (Lógica do Usuário) - VETORIZADO
    # -------------------------------------------------------------------------
    
    # Preencher nulos iniciais
    cols_to_check = ["EmPrEP_Atual", "Disp_Ultimos_12m"]
    for c in cols_to_check:
        if c not in df_disp_semdupl.columns: df_disp_semdupl[c] = None
        
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
        
        # Garantir existência
        if col_emprep not in df_disp_semdupl.columns: df_disp_semdupl[col_emprep] = None
        if col_disp12m not in df_disp_semdupl.columns: df_disp_semdupl[col_disp12m] = None
        
        cond_ano = [
            df_disp_semdupl[col_emprep] == f"Em PrEP {ano_e}",
            (df_disp_semdupl[col_disp12m] == f"Teve dispensação em {ano_e}") & (df_disp_semdupl[col_emprep].isna())
        ]
        choices_ano = [f"Em PrEP {ano_e}", f"Descontinuou em {ano_e}"]
        
        df_disp_semdupl[col_emprep] = np.select(cond_ano, choices_ano, default=None)

    return df_disp_semdupl, EmPrEP_monthly_sample

def generate_prep_history_legacy(df_disp_semdupl, data_fechamento):
    """
    [LEGACY] Gera histórico mensal detalhado de adesão (Em PrEP vs Descontinuados).
    Mantido para validação de equivalência.
    """
    print("Gerando histórico detalhado mensal (LEGACY - Lento)...")
    
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

def generate_annual_summary(df_prep, data_fechamento):
    """
    Gera tabela resumo anual (2018-Atual):
    Ano | Disp 12m | Em PrEP | %
    """
    print("Gerando resumo anual (Aba 'Em PrEP por ano')...")
    
    hoje_dt = pd.to_datetime(data_fechamento)
    anos = range(2018, hoje_dt.year + 1)
    
    rows = []
    for ano in anos:
        col_disp = f"Disp_12m_{ano}"
        col_emprep = f"EmPrEP_{ano}"
        
        # Contagem Disp 12m
        if col_disp in df_prep.columns:
            # String exata definida em generate_prep_history
            count_disp = len(df_prep[df_prep[col_disp] == f'Teve dispensação em {ano}'])
        else:
            count_disp = 0
            
        # Contagem Em PrEP
        if col_emprep in df_prep.columns:
            count_emprep = len(df_prep[df_prep[col_emprep] == f'Em PrEP {ano}'])
        else:
            count_emprep = 0
            
        # Porcentagem
        perc = (count_emprep / count_disp * 100) if count_disp > 0 else 0
        
        rows.append({
            "Ano": ano,
            "Pelo menos uma dispensação nos últimos 12 meses": count_disp,
            "Em PrEP": count_emprep,
            "% Em PrEP": round(perc, 1)
        })
        
    return pd.DataFrame(rows)