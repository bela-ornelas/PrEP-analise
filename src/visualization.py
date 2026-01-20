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
