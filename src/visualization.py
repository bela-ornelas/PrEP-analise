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
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(18, 8))
    
    colors = ['#DCE6F2', '#95B3D7', '#4F81BD', '#1F497D', '#95B3D7', '#4F81BD']
    unique_years = crosstab_long['Year'].unique()
    
    # Garantir Ordem Cronológica para Plotagem
    month_map = {m: i for i, m in enumerate(MONTHS_ORDER)}
    crosstab_long['month_num'] = crosstab_long['Month'].map(month_map)
    crosstab_long = crosstab_long.sort_values(['Year', 'month_num'])
    crosstab_long['x_label'] = crosstab_long['Month'] + " " + crosstab_long['Year']
    
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

    # 4. Anotações
    crosstab_long = crosstab_long.reset_index(drop=True)
    for idx, row in crosstab_long.iterrows():
        should_annotate = False
        if row['Month'] == 'Dez': should_annotate = True
        if row['Year'] == current_year_str and row['Month'] == current_month_abbr: should_annotate = True
            
        if should_annotate:
            val = row['Count']
            val_str = "{:,}".format(val).replace(",", ".")
            ax.text(idx, val + 500, val_str, color='black', ha='center', va='bottom', fontsize=12)

    # 5. Ajustar Labels X
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

    if not os.path.exists(output_dir): os.makedirs(output_dir)
    save_path = os.path.join(output_dir, "PrEP_disp.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)

def plot_cascade(df_prep, output_dir):
    print("Gerando gráfico: Cascata PrEP...")
    total_registros = len(df_prep)
    soma_disp2 = df_prep['dt_disp_min'].notnull().sum()
    count_disp12m = (df_prep['Disp_Ultimos_12m'] == 'Teve dispensação nos últimos 12 meses').sum()
    count_emprep = (df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente').sum()
    count_desc = (df_prep['EmPrEP_Atual'] == 'Estão descontinuados').sum()

    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(10, 6))
    bar_width = 0.4
    
    x_pos = np.arange(5)
    counts = [total_registros, soma_disp2, count_disp12m, count_emprep, count_desc]
    labels = ['Procuraram PrEP', 'Iniciaram PrEP', 'Dispensação\núltimos 12m', 'Em PrEP', 'Descontinuados']
    colors = ['#B7DEE8', '#31859C', '#376092', '#215968', '#C0504D']
    
    bars = ax.bar(x_pos, counts, width=bar_width, color=colors, edgecolor='none')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, '{:,.0f}'.format(height).replace(",", "."),
                ha='center', va='bottom', fontsize=12)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.yaxis.set_ticks([])
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10)
    plt.tick_params(axis='x', which='both', bottom=False)
    plt.tight_layout()
    
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    save_path = os.path.join(output_dir, "PrEP_cascata.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)

def plot_prep_annual_summary(df_prep, data_fechamento, output_dir):
    print("Gerando gráfico: Usuários em PrEP por ano...")
    hoje_dt = pd.to_datetime(data_fechamento)
    current_year = hoje_dt.year
    years = np.arange(2018, current_year + 1)
    
    prep_counts = []
    total_counts = [] 
    
    for year in years:
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
            n_emprep, n_total = 0, 0
            
        prep_counts.append(n_emprep)
        total_counts.append(n_total)
        
    prep_counts = np.array(prep_counts)
    total_counts = np.array(total_counts)
    
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(12, 6))
    bar_width = 0.35
    opacity = 0.8
    
    bars_total = ax.bar(years - bar_width / 2, total_counts, width=bar_width, 
                         label='Pelo menos uma dispensação nos últimos 12 meses', 
                         alpha=opacity, color='#376092')
    
    bars_usage = ax.bar(years + bar_width / 2, prep_counts, width=bar_width, 
                         label='Em PrEP', alpha=opacity, color='#215968')
                         
    for bars in [bars_total, bars_usage]:
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 100, f'{yval:,.0f}'.replace(",", "."), ha='center', va='bottom')
            
    for i, bar in enumerate(bars_usage):
        if total_counts[i] > 0:
            perc = (prep_counts[i] / total_counts[i]) * 100
            y_pos = bar.get_height() * 0.02 
            ax.text(bar.get_x() + bar.get_width()/2, y_pos, f'{perc:.0f}%', 
                    ha='center', va='bottom', color='white', fontsize=11, fontweight='bold')

    ax.get_yaxis().set_visible(False)
    ax.set_xticks(years)
    ax.legend(frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    plt.tick_params(axis='x', which='both', bottom=False)
    
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    save_path = os.path.join(output_dir, "PrEP_emprep.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)

def plot_new_users(df_prep, data_fechamento, output_dir):
    print("Gerando gráfico: Novos Usuários por Mês/Ano...")
    hoje_dt = pd.to_datetime(data_fechamento)
    
    if 'dt_disp_min' not in df_prep.columns: return
        
    filtered = df_prep[df_prep['dt_disp_min'].notnull()].copy()
    filtered['ano_pri_disp'] = filtered['dt_disp_min'].dt.year.astype(str)
    
    month_map_num_en = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
    filtered['mes_pri_disp_en'] = filtered['dt_disp_min'].dt.month.map(month_map_num_en)

    crosstab_result = pd.crosstab(index=filtered['mes_pri_disp_en'], columns=filtered['ano_pri_disp'])
    months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    crosstab_result = crosstab_result.reindex(months_order)
    
    crosstab_long = crosstab_result.reset_index().melt(id_vars='mes_pri_disp_en', value_name='Count')
    crosstab_long.columns = ['Month', 'Year', 'Count']
    crosstab_long = crosstab_long[crosstab_long['Count'] != 0].copy()
    
    months_pt = {'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr', 'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago', 'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'}
    crosstab_long['Month_PT'] = crosstab_long['Month'].map(months_pt)
    crosstab_long['x_label'] = crosstab_long['Month_PT'] + " " + crosstab_long['Year']
    
    month_map_sort = {m: i for i, m in enumerate(months_order)}
    crosstab_long['month_num'] = crosstab_long['Month'].map(month_map_sort)
    crosstab_long['Year_Int'] = crosstab_long['Year'].astype(int)
    crosstab_long = crosstab_long.sort_values(['Year_Int', 'month_num']).reset_index(drop=True)

    current_month_en = month_map_num_en[hoje_dt.month]
    current_year_str = str(hoje_dt.year)
    
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(18, 8))
    colors = ['#DBEEF4', '#93CDDD', '#4BACC6', '#215968']
    unique_years = crosstab_long['Year'].unique()
    
    for i, year in enumerate(unique_years):
        data_year = crosstab_long[crosstab_long['Year'] == year]
        color = colors[i % len(colors)]
        ax.bar(data_year['x_label'], data_year['Count'], color=color)

    ax.yaxis.set_visible(False)
    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.tick_params(axis='x', which='both', bottom=False)

    for idx, row in crosstab_long.iterrows():
        should_annotate = False
        if row['Month'] == 'Dec': should_annotate = True
        if row['Year'] == current_year_str and row['Month'] == current_month_en: should_annotate = True
        if should_annotate:
            v = row['Count']
            ax.text(idx, v + 200, f"{v:,.0f}".replace(",", "."), color='black', ha='center', va='bottom', fontsize=12)

    events = {
        'Mar 2020': 'Março 2020:\n OMS declara \n pandemia de COVID-19',
        'Jun 2021': 'Junho 2021:\n Início da expansão \n para serviços privados',
        'Jul 2021': 'Julho 2021:\n Simplificação da ficha',
        'Aug 2022': 'Agosto 2022:\n Atualização PCDT \n (ampliação da indicação)',
        'Dec 2022': 'Dezembro 2022:\n PrEP sob demanda',
        'Feb 2024': 'Fevereiro 2024:\n  autoteste de HIV p/\n PrEP teleatendimento'
    }

    y_max = crosstab_long['Count'].max()
    ax.set_ylim(0, y_max * 1.4) 
    
    for i, (date_str, text) in enumerate(events.items()):
        e_month, e_year = date_str.split(' ')
        match = crosstab_long[(crosstab_long['Month'] == e_month) & (crosstab_long['Year'] == e_year)]
        if not match.empty:
            idx = match.index[0]
            text_y = ax.get_ylim()[1] * 0.80 if i % 2 == 0 else ax.get_ylim()[1] * 0.65
            line_ymax = text_y - (y_max * 0.1)
            ax.vlines(x=idx, ymin=0, ymax=line_ymax, linestyle='dotted', color='#F4B183')
            ax.text(idx, text_y, text, color='#7F7F7F', ha='center', fontsize=9)

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

    if not os.path.exists(output_dir): os.makedirs(output_dir)
    save_path = os.path.join(output_dir, "PrEP_novosusuarios.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar gráfico: {e}")
    finally:
        plt.close(fig)

def plot_horizontal_bars(df_prep, col_name, filename, output_dir, color='#215968', show_percentage=False, filter_others=False):
    """
    Gera gráficos de barras horizontais para demografia.
    """
    if df_prep.empty or col_name not in df_prep.columns:
        print(f"Skipping plot {filename}: column {col_name} missing.")
        return

    # Filtra apenas ativos
    if 'EmPrEP_Atual' in df_prep.columns:
        df_active = df_prep[df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente']
    else:
        df_active = df_prep
        
    counts = df_active[col_name].value_counts().sort_values(ascending=False)
    
    if filter_others and 'Outros' in counts.index:
        counts = counts.drop('Outros')
    
    if counts.empty: return

    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.barh(counts.index.astype(str), counts.values, color=color)
    total = counts.sum()
    
    for i, bar in enumerate(bars):
        width = bar.get_width()
        if show_percentage:
            label = f"{(width/total*100):.1f}%".replace('.', ',')
        else:
            label = f"{int(width):,}".replace(",", ".")
        offset = counts.max() * 0.01
        ax.text(width + offset, bar.get_y() + bar.get_height()/2, label, va='center', fontsize=12)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False) 
    ax.xaxis.set_visible(False) 
    plt.tight_layout()
    
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    save_path = os.path.join(output_dir, filename)
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar {filename}: {e}")
    finally:
        plt.close(fig)

def plot_vertical_bars(df_prep, col_name, filename, output_dir, color='#254061', show_percentage=False, filter_ignored=False, custom_order=None):
    if df_prep.empty or col_name not in df_prep.columns: return

    if 'EmPrEP_Atual' in df_prep.columns:
        df_active = df_prep[df_prep['EmPrEP_Atual'] == 'Em PrEP atualmente']
    else:
        df_active = df_prep
        
    counts = df_active[col_name].value_counts()
    
    if custom_order:
        counts = counts.reindex(custom_order).fillna(0)
    else:
        if df_active[col_name].dtype.name == 'category':
            counts = counts.sort_index()
        else:
            counts = counts.sort_index()
        
    if filter_ignored:
        counts = counts[~counts.index.astype(str).str.contains("Ignorada|Não informada", case=False, na=False)]
    
    if counts.empty: return

    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(counts.index.astype(str), counts.values, color=color)
    total = counts.sum()
    
    for bar in bars:
        height = bar.get_height()
        if show_percentage:
            label = f"{(height/total*100):.1f}%".replace('.', ',')
        else:
            label = f"{int(height):,}".replace(",", ".")
        ax.text(bar.get_x() + bar.get_width()/2, height + (counts.max()*0.01), label, ha='center', va='bottom', fontsize=12)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False) 
    ax.yaxis.set_visible(False) 
    plt.tight_layout()
    
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    save_path = os.path.join(output_dir, filename)
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar {filename}: {e}")
    finally:
        plt.close(fig)

def plot_modalities(df_disp_semdupl, output_dir):
    print("Gerando gráfico: Modalidades (recomendadoXrealizado)...")
    if df_disp_semdupl.empty or 'recomendadoXrealizado' not in df_disp_semdupl.columns:
        print("Aviso: Coluna 'recomendadoXrealizado' não encontrada para o gráfico.")
        return

    filtered_data = df_disp_semdupl[df_disp_semdupl['recomendadoXrealizado'] != 'primeira dispensa'].copy()
    if filtered_data.empty: return

    value_counts2 = filtered_data['recomendadoXrealizado'].value_counts(dropna=True)
    value_counts_percentage2 = filtered_data['recomendadoXrealizado'].value_counts(dropna=True, normalize=True) * 100
    
    # Montar DF para plotagem
    tab = pd.DataFrame({
        'Counts': value_counts2,
        'Percentage (%)': value_counts_percentage2
    }).sort_values(by='Percentage (%)', ascending=False) # Maior embaixo (index 0 no barh fica na base)

    # 3. Plotting

    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(12, 7))
    
    bars = ax.barh(tab.index.astype(str), tab['Percentage (%)'], color='teal')
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.2, bar.get_y() + bar.get_height()/2, f"{width:.1f}%", va='center', color='black', fontsize=14)

    total_count = tab['Counts'].sum()
    formatted_number = "{:,}".format(total_count).replace(',', '.')
    ax.text(0.7, 0.8, f"N = {formatted_number}", transform=ax.transAxes, fontsize=14, va='bottom', ha='left', color='black')

    ax.grid(False)
    ax.set_xticklabels([])
    ax.set_xlabel('')
    ax.tick_params(axis='y', labelsize=15)
    plt.tick_params(axis='x', which='both', bottom=False)
    plt.tick_params(axis='y', which='both', left=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(True)
    ax.spines['bottom'].set_visible(False)
    plt.tight_layout()
    
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    save_path = os.path.join(output_dir, "PrEP_modalidades.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar modalidades: {e}")
    finally:
        plt.close(fig)

def plot_ist_metrics(df_disp_semdupl, output_dir):
    print("Gerando gráfico: Métricas de IST...")
    name_mapping = {
        'st_ferida_vagina_penis': 'Feridas na vagina/ no pênis',
        'st_ferida_anus': 'Feridas no ânus',
        'st_verruga_vagina_penis': 'Verrugas na vagina/no pênis',
        'st_verruga_anus': 'Verrugas no ânus',
        'st_bolhas_vagina_penis': 'Pequenas bolhas na vagina/no pênis',
        'st_bolhas_anus': 'Pequenas bolhas no ânus',
        'st_corrimento_vaginal': 'Corrimento vaginal ou no canal uretral',
        'st_sifilis': 'Diagnóstico de Sífilis',
        'st_gonorreia_clamidia': 'Diagnóstico de Gonorréia/Clamídia Retal',
        'st_suspeita_mpox': 'Suspeita de Mpox',
        'st_diagnost_mpox' : 'Diagnóstico de Mpox'
    }
    cols_to_sum = [c for c in name_mapping.keys() if c in df_disp_semdupl.columns]
    if not cols_to_sum: return
        
    column_sums = df_disp_semdupl[cols_to_sum].sum().sort_values(ascending=True)
    
    if 'IST_autorrelato' in df_disp_semdupl.columns:
        denominator = df_disp_semdupl["IST_autorrelato"].notna().sum()
    else:
        denominator = len(df_disp_semdupl)
    if denominator == 0: denominator = 1 

    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize=(10, 7))
    
    y_labels = [name_mapping.get(idx, idx) for idx in column_sums.index]
    bars = ax.barh(y_labels, column_sums.values, color='#953735')
    
    for bar in bars:
        width = bar.get_width()
        porcentagem = f"{width / denominator:.1%}".replace(".", ",")
        ax.text(width + (column_sums.max() * 0.01), bar.get_y() + bar.get_height()/2, porcentagem, va='center', color='black', fontsize=12)

    ax.grid(False)
    ax.set_xticklabels([])
    ax.xaxis.set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(True)
    plt.tick_params(axis='x', which='both', bottom=False)
    plt.tick_params(axis='y', which='both', left=False)
    plt.tight_layout()
    
    if not os.path.exists(output_dir): os.makedirs(output_dir)
        
    save_path = os.path.join(output_dir, "PrEP_IST.png")
    try:
        fig.savefig(save_path, facecolor='white', transparent=False, bbox_inches='tight')
        print(f"Gráfico salvo: {save_path}")
    except Exception as e:
        print(f"Erro ao salvar IST: {e}")
    finally:
        plt.close(fig)