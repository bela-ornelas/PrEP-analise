import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np
from .config import MONTHS_ORDER

def plot_dispensations(df_disp_semdupl, data_fechamento, output_dir):
    """
    Gera o gráfico de barras de Dispensas de PrEP por Mês/Ano.
    Salva como 'PrEP_disp.png'.
    """
    print("Gerando gráfico: Dispensas por Mês/Ano...")
    
    # Garantir datetime
    hoje_dt = pd.to_datetime(data_fechamento)
    
    # 1. Preparar Dados (Crosstab + Melt)
    crosstab_result = pd.crosstab(index=df_disp_semdupl['mes_disp'], 
                                  columns=df_disp_semdupl['ano_disp'])
    
    # Reindexar meses
    crosstab_result = crosstab_result.reindex(MONTHS_ORDER)
    
    # Converter para formato longo
    crosstab_long = crosstab_result.reset_index().melt(id_vars='mes_disp', value_name='Count')
    crosstab_long.columns = ['Month', 'Year', 'Count']
    
    # Ajuste de tipos
    crosstab_long['Year'] = crosstab_long['Year'].astype(int).astype(str)
    
    # Remover linhas zeradas (conforme script original)
    crosstab_long = crosstab_long[crosstab_long['Count'] != 0].copy()
    
    # Identificar Mês Atual para anotação
    current_month_abbr = MONTHS_ORDER[hoje_dt.month - 1]
    current_year_str = str(hoje_dt.year)

    # 2. Plotting
    # Usar estilo 'default' ou configurar manualmente os params para evitar conflito com notebooks
    plt.rcParams.update(plt.rcParamsDefault)
    
    fig, ax = plt.subplots(figsize=(18, 8))
    
    # Colors Palette
    colors = ['#DCE6F2', '#95B3D7', '#4F81BD', '#1F497D', '#95B3D7', '#4F81BD']
    
    unique_years = crosstab_long['Year'].unique()
    
    # Garantir Ordem Cronológica para Plotagem
    month_map = {m: i for i, m in enumerate(MONTHS_ORDER)}
    crosstab_long['month_num'] = crosstab_long['Month'].map(month_map)
    crosstab_long = crosstab_long.sort_values(['Year', 'month_num'])
    
    # Criar label composta para o eixo X
    crosstab_long['x_label'] = crosstab_long['Month'] + " " + crosstab_long['Year']
    
    # Loop de plotagem (Ano a Ano para manter cores cíclicas)
    for i, year in enumerate(unique_years):
        data_year = crosstab_long[crosstab_long['Year'] == year]
        color = colors[i % len(colors)]
        ax.bar(data_year['x_label'], data_year['Count'], color=color)

    # 3. Estilização
    ax.yaxis.set_visible(False)
    ax.grid(False)
    
    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    
    # Ticks
    ax.tick_params(axis='x', which='both', bottom=False)

    # 4. Anotações
    crosstab_long = crosstab_long.reset_index(drop=True)
    
    for idx, row in crosstab_long.iterrows():
        should_annotate = False
        
        # Regra: Dezembro OU Mês Atual (do ano atual)
        if row['Month'] == 'Dez':
            should_annotate = True
        
        if row['Year'] == current_year_str and row['Month'] == current_month_abbr:
            should_annotate = True
            
        if should_annotate:
            val = row['Count']
            val_str = "{:,}".format(val).replace(",", ".")
            ax.text(idx, val + 500, val_str, color='black', ha='center', va='bottom', fontsize=12)

    # 5. Ajustar Labels X (Anos centralizados)
    new_xticks_pos = []
    new_xticks_labels = []
    
    current_x_pos = 0
    for year in unique_years:
        count_months = len(crosstab_long[crosstab_long['Year'] == year])
        # Centro do grupo
        center = current_x_pos + (count_months - 1) / 2
        new_xticks_pos.append(center)
        new_xticks_labels.append(year)
        current_x_pos += count_months

    plt.xticks(new_xticks_pos, new_xticks_labels, rotation=0)

    # Salvar
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    save_path = os.path.join(output_dir, "PrEP_disp.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo em: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)

def plot_cascade(df_prep, output_dir):
    """
    Gera o gráfico de Cascata PrEP a partir do dataframe consolidado.
    Salva como 'PrEP_cascata.png'.
    """
    print("Gerando gráfico: Cascata PrEP...")
    
    # 1. Cálculos
    total_registros = len(df_prep)  # Procuraram PrEP
    soma_disp2 = df_prep['dt_disp_min'].notnull().sum()  # Iniciaram PrEP (Data da primeira dispensa existe)
    
    count_disp12m = (df_prep['Disp_Ultimos_12m'] == 'Teve dispensação nos últimos 12 meses').sum()
    count_emprep = (df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente').sum()
    count_desc = (df_prep['EmPrEP_Atual'] == 'Estão descontinuados').sum()

    # 2. Plotting
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(10, 6))
    bar_width = 0.4
    
    # Coordenadas X fixas para simplicidade (mantendo a lógica de cascata)
    x_pos = np.arange(5)
    counts = [total_registros, soma_disp2, count_disp12m, count_emprep, count_desc]
    labels = ['Procuraram PrEP', 'Iniciaram PrEP', 'Dispensação\núltimos 12m', 'Em PrEP', 'Descontinuados']
    colors = ['#B7DEE8', '#31859C', '#376092', '#215968', '#C0504D']
    
    bars = ax.bar(x_pos, counts, width=bar_width, color=colors, edgecolor='none')
    
    # 3. Anotações (Valores acima das barras)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height,
                '{:,.0f}'.format(height).replace(",", "."),
                ha='center', va='bottom', fontsize=12)

    # 4. Estilização
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    
    ax.yaxis.set_ticks([])
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10)
    
    plt.tick_params(axis='x', which='both', bottom=False)
    plt.tight_layout()
    
    # 5. Salvar
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    save_path = os.path.join(output_dir, "PrEP_cascata.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo em: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)

def plot_prep_annual_summary(df_prep, data_fechamento, output_dir):
    """
    Gera o gráfico de barras agrupadas: 'Pelo menos uma disp 12m' vs 'Em PrEP'.
    Salva como 'PrEP_emprep.png'.
    """
    print("Gerando gráfico: Usuários em PrEP por ano (Barras Agrupadas)...")
    
    hoje_dt = pd.to_datetime(data_fechamento)
    current_year = hoje_dt.year
    years = np.arange(2018, current_year + 1)
    
    # Preparar Dados
    prep_counts = []
    total_counts = [] # (Em PrEP + Descontinuou) = Pelo menos uma dispensa
    
    for year in years:
        # Lógica de nomes de colunas conforme gerado em analysis.py
        if year == current_year:
            col_name = "EmPrEP_Atual"
            val_emprep = "Em PrEP atualmente"
            val_descontinuou = "Estão descontinuados"
        else:
            col_name = f"EmPrEP_{year}"
            val_emprep = f"Em PrEP {year}"
            val_descontinuou = f"Descontinuou em {year}"
            
        if col_name in df_prep.columns:
            n_emprep = len(df_prep[df_prep[col_name] == val_emprep])
            n_descontinuou = len(df_prep[df_prep[col_name] == val_descontinuou])
            n_total = n_emprep + n_descontinuou
        else:
            n_emprep = 0
            n_total = 0
            
        prep_counts.append(n_emprep)
        total_counts.append(n_total)
        
    prep_counts = np.array(prep_counts)
    total_counts = np.array(total_counts)
    
    # Plotting
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bar_width = 0.35
    opacity = 0.8
    
    # Bars
    bars_total = ax.bar(years - bar_width / 2, 
                         total_counts, 
                         width=bar_width, 
                         label='Pelo menos uma dispensação nos últimos 12 meses', 
                         alpha=opacity, 
                         color='#376092')
    
    bars_usage = ax.bar(years + bar_width / 2, 
                         prep_counts, 
                         width=bar_width, 
                         label='Em PrEP', 
                         alpha=opacity, 
                         color='#215968')
                         
    # Labels (Topo das barras)
    for bars in [bars_total, bars_usage]:
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 100, 
                    f'{yval:,.0f}'.replace(",", "."), 
                    ha='center', va='bottom')
                    
    # [NOVO] Porcentagem na base da barra "Em PrEP"
    for i, bar in enumerate(bars_usage):
        if total_counts[i] > 0:
            perc = (prep_counts[i] / total_counts[i]) * 100
            # Exibir na base (aprox 2% da altura ou fixo se preferir)
            # Usando um offset fixo pequeno para garantir que fique dentro mesmo se a barra for pequena,
            # mas alto o suficiente para ler. Vamos usar 5% da altura da própria barra.
            y_pos = bar.get_height() * 0.02 
            # Se a barra for muito baixa, o texto pode vazar, mas para esses volumes (milhares) é ok.
            
            ax.text(bar.get_x() + bar.get_width()/2, y_pos, 
                    f'{perc:.0f}%', 
                    ha='center', va='bottom', color='white', fontsize=11, fontweight='bold')

    # Estilização
    ax.get_yaxis().set_visible(False)
    ax.set_xticks(years)
    
    # Legend
    ax.legend(frameon=False)
    
    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    
    plt.tick_params(axis='x', which='both', bottom=False)
    
    # Save
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)

def plot_new_users(df_prep, data_fechamento, output_dir):
    """
    Gera o gráfico de Novos Usuários por Mês/Ano com marcos históricos.
    Salva como 'PrEP_novosusuarios.png'.
    """
    print("Gerando gráfico: Novos Usuários por Mês/Ano...")
    
    hoje_dt = pd.to_datetime(data_fechamento)
    
    # 1. Filtro e Preparação
    if 'dt_disp_min' not in df_prep.columns:
        print("Aviso: 'dt_disp_min' não encontrada. Pulando gráfico de novos usuários.")
        return
        
    filtered = df_prep[df_prep['dt_disp_min'].notnull()].copy()
    
    # Garantir colunas de mês/ano da primeira dispensa
    filtered['ano_pri_disp'] = filtered['dt_disp_min'].dt.year.astype(str)
    
    # Mapeamento manual de mês numérico para EN (para garantir ordem)
    month_map_num_en = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 
                        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
    filtered['mes_pri_disp_en'] = filtered['dt_disp_min'].dt.month.map(month_map_num_en)

    # Crosstab
    crosstab_result = pd.crosstab(index=filtered['mes_pri_disp_en'], 
                                  columns=filtered['ano_pri_disp'])
    
    # Reindexar Meses
    months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    crosstab_result = crosstab_result.reindex(months_order)
    
    # Melt
    crosstab_long = crosstab_result.reset_index().melt(id_vars='mes_pri_disp_en', value_name='Count')
    crosstab_long.columns = ['Month', 'Year', 'Count']
    
    # Remover zerados
    crosstab_long = crosstab_long[crosstab_long['Count'] != 0].copy()
    
    # Traduzir Meses
    months_pt = {
        'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr', 'May': 'Mai', 'Jun': 'Jun',
        'Jul': 'Jul', 'Aug': 'Ago', 'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
    }
    crosstab_long['Month_PT'] = crosstab_long['Month'].map(months_pt)
    crosstab_long['x_label'] = crosstab_long['Month_PT'] + " " + crosstab_long['Year']
    
    # Garantir Ordem Cronológica para Plotagem
    month_map_sort = {m: i for i, m in enumerate(months_order)}
    crosstab_long['month_num'] = crosstab_long['Month'].map(month_map_sort)
    crosstab_long['Year_Int'] = crosstab_long['Year'].astype(int)
    crosstab_long = crosstab_long.sort_values(['Year_Int', 'month_num'])
    crosstab_long = crosstab_long.reset_index(drop=True)

    # Identificar Mês Atual (Referência)
    current_month_en = month_map_num_en[hoje_dt.month]
    current_year_str = str(hoje_dt.year)
    
    # 2. Plotting
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(18, 8))
    
    colors = ['#DBEEF4', '#93CDDD', '#4BACC6', '#215968']
    
    unique_years = crosstab_long['Year'].unique()
    
    for i, year in enumerate(unique_years):
        data_year = crosstab_long[crosstab_long['Year'] == year]
        color = colors[i % len(colors)]
        ax.bar(data_year['x_label'], data_year['Count'], color=color)

    # 3. Estilização
    ax.yaxis.set_visible(False)
    ax.grid(False)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    
    ax.tick_params(axis='x', which='both', bottom=False)

    # 4. Anotações (Dezembro e Mês Atual)
    for idx, row in crosstab_long.iterrows():
        should_annotate = False
        
        if row['Month'] == 'Dec': # Usando EN
            should_annotate = True
        
        if row['Year'] == current_year_str and row['Month'] == current_month_en:
            should_annotate = True
            
        if should_annotate:
            v = row['Count']
            ax.text(idx, v + 200, f"{v:,.0f}".replace(",", "."), 
                    color='black', ha='center', va='bottom', fontsize=12)

    # 5. Marcos Históricos (Linhas Verticais)
    events = {
        'Mar 2020': 'Março 2020:\n OMS declara \n pandemia de COVID-19',
        'Jun 2021': 'Junho 2021:\n Início da expansão \n para serviços privados',
        'Jul 2021': 'Julho 2021:\n Simplificação da ficha',
        'Aug 2022': 'Agosto 2022:\n Atualização PCDT \n (ampliação da indicação)',
        'Dec 2022': 'Dezembro 2022:\n PrEP sob demanda',
        'Feb 2024': 'Fevereiro 2024:\n  autoteste de HIV p/\n PrEP teleatendimento'
    }

    # Ajuste manual do limite Y para caber texto
    y_max = crosstab_long['Count'].max()
    ax.set_ylim(0, y_max * 1.4) 
    
    for i, (date_str, text) in enumerate(events.items()):
        e_month, e_year = date_str.split(' ')
        match = crosstab_long[(crosstab_long['Month'] == e_month) & (crosstab_long['Year'] == e_year)]
        
        if not match.empty:
            idx = match.index[0]
            
            # Linha Vertical
            ax.axvline(idx, linestyle='dotted', color='#F4B183', ymin=0, ymax=0.90)
            
            # Texto alternado
            text_y = ax.get_ylim()[1] * 0.80 if i % 2 == 0 else ax.get_ylim()[1] * 0.65
            ax.text(idx, text_y, text, color='#7F7F7F', ha='center', fontsize=9)

    # 6. Labels X Agrupados (Ano)
    new_xticks_pos = []
    new_xticks_labels = []
    
    current_x_pos = 0
    for year in unique_years:
        count_months = len(crosstab_long[crosstab_long['Year'] == year])
        center = current_x_pos + (count_months - 1) / 2
        new_xticks_pos.append(center)
        new_xticks_labels.append(year)
        current_x_pos += count_months

    plt.xticks(new_xticks_pos, new_xticks_labels, rotation=0)

    # Salvar
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    save_path = os.path.join(output_dir, "PrEP_novosusuarios.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo em: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)
