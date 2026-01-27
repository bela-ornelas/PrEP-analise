import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
import numpy as np

# Adiciona diretório atual ao path para imports
sys.path.append(os.getcwd())

# Tenta importar as funções do script original
try:
    from analise_perfis_engajamento_prep import classificar_comportamento, executar_regressao_multinomial
    from src.data_loader import carregar_bases
    from src.cleaning import clean_disp_df, process_cadastro
    from src.preprocessing import calculate_population_groups, enrich_disp_data
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)

def plot_stacked_bars(df):
    print("Gerando Gráfico de Barras Empilhadas...")
    
    # Criar Crosstab
    ct = pd.crosstab(df['Pop_genero_pratica'], df['perfil_uso'], normalize='index') * 100
    
    # Remover categorias irrelevantes se existirem
    if 'Outros' in ct.index: ct = ct.drop('Outros')
    if 'Ignorado' in ct.index: ct = ct.drop('Ignorado')
    
    # Ordenar por 'Sustained' para dar um visual de "ranking"
    if 'Sustained' in ct.columns:
        ct = ct.sort_values('Sustained', ascending=True)
    
    # Cores personalizadas
    # Discontinued: Vermelho/Laranja, Cyclic: Amarelo, Sustained: Verde/Azul
    # A ordem das colunas geralmente é alfabética: Cyclic, Discontinued, Sustained
    # Vamos forçar a ordem para garantir as cores
    cols_order = ['Discontinued', 'Cyclic', 'Sustained']
    cols_present = [c for c in cols_order if c in ct.columns]
    ct = ct[cols_present]
    
    colors_map = {
        'Discontinued': '#e74c3c', # Vermelho
        'Cyclic': '#f1c40f',      # Amarelo
        'Sustained': '#2ecc71'    # Verde
    }
    colors = [colors_map.get(c, 'gray') for c in cols_present]
    
    plt.figure(figsize=(12, 8))
    ax = ct.plot(kind='barh', stacked=True, color=colors, figsize=(12, 8), edgecolor='white')
    
    plt.title('Perfis de Engajamento em PrEP por População', fontsize=16)
    plt.xlabel('Porcentagem (%)', fontsize=12)
    plt.ylabel('')
    plt.legend(title='Perfil', bbox_to_anchor=(1.01, 1), loc='upper left')
    
    # Adicionar rótulos de dados
    for n, x in enumerate([*ct.index.values]):
        for (cn, y) in enumerate(ct.iloc[n]):
            if y > 5: # Só mostra se for maior que 5% para não poluir
                # Calcular posição x (acumulada)
                cum = ct.iloc[n][:cn].sum()
                plt.text(cum + y/2, n, f'{y:.0f}%', va='center', ha='center', color='black', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('grafico_perfis_populacao.png', dpi=300)
    print("Salvo: grafico_perfis_populacao.png")
    plt.close()

def plot_forest(df_reg_results):
    if df_reg_results is None or df_reg_results.empty:
        print("Sem dados de regressão para plotar Forest Plot.")
        return

    print("Gerando Forest Plots...")
    
    outcomes = df_reg_results['Outcome'].unique()
    
    for outcome in outcomes:
        data = df_reg_results[df_reg_results['Outcome'] == outcome].copy()
        
        # Filtrar Intercepto se houver
        data = data[~data['Variable_Clean'].str.contains('Intercept')]
        
        # Inverter ordem para plotar de cima para baixo
        data = data.iloc[::-1]
        
        plt.figure(figsize=(10, len(data) * 0.4 + 2))
        
        # Pontos (Odds Ratio) e Barras de Erro (IC)
        # y: indice, x: aOR
        y_pos = np.arange(len(data))
        
        # Cor baseada na significância
        colors = ['red' if p < 0.05 else 'gray' for p in data['p_value']]
        
        plt.errorbar(data['aOR'], y_pos, xerr=[data['aOR'] - data['CI_Lower'], data['CI_Upper'] - data['aOR']], 
                     fmt='o', color='black', ecolor=colors, capsize=3, elinewidth=1.5, markeredgewidth=0)
        
        plt.yticks(y_pos, data['Variable_Clean'])
        plt.axvline(x=1, color='black', linestyle='--', linewidth=0.8)
        
        plt.xlabel('Adjusted Odds Ratio (log scale)')
        plt.title(f'Multinomial Regression: {outcome}\n(Ref: Sustained Use)', fontsize=14)
        plt.xscale('log')
        
        # Ajustar limites do x para ficar bonito
        plt.xlim(min(data['CI_Lower'].min() * 0.8, 0.1), max(data['CI_Upper'].max() * 1.1, 10))
        
        plt.grid(axis='x', linestyle=':', alpha=0.5)
        plt.tight_layout()
        
        safe_name = outcome.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '')
        plt.savefig(f'grafico_forest_{safe_name}.png', dpi=300)
        print(f"Salvo: grafico_forest_{safe_name}.png")
        plt.close()

def main():
    DATA_FECHAMENTO = '2025-12-31'
    
    # 1. Carregar e Processar (Mesma lógica do script original)
    print("Carregando dados...")
    bases = carregar_bases(pd.to_datetime(DATA_FECHAMENTO).date(), use_cache=True)
    df_disp = bases.get("Disp", pd.DataFrame())
    df_cad_prep = bases.get("Cadastro_PrEP", pd.DataFrame())
    
    df_disp, df_disp_semdupl = clean_disp_df(df_disp, DATA_FECHAMENTO)
    df_cad_prep = process_cadastro(df_cad_prep)
    df_disp_semdupl = enrich_disp_data(df_disp_semdupl, df_cad_prep, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    
    try:
        df_cad_prep = calculate_population_groups(df_cad_prep)
    except: pass
    
    # 2. Classificar
    df_classificacao = classificar_comportamento(df_disp_semdupl, DATA_FECHAMENTO)
    df_final = df_classificacao.merge(df_cad_prep, on='codigo_pac_eleito', how='left')
    
    # Recalcular Faixa Etária e Idade para garantir consistência
    hoje = pd.to_datetime(DATA_FECHAMENTO)
    if 'data_nascimento' in df_final.columns:
        df_final['data_nascimento'] = pd.to_datetime(df_final['data_nascimento'], errors='coerce')
        df_final['idade'] = (hoje - df_final['data_nascimento']) / pd.to_timedelta(365.25, unit='D')
        bins = [0, 18, 24, 29, 39, 49, 100]
        labels = ['<18', '18-24', '25-29', '30-39', '40-49', '50+']
        df_final['faixa_etaria'] = pd.cut(df_final['idade'], bins=bins, labels=labels)

    # 3. Plotar Barras
    plot_stacked_bars(df_final)
    
    # 4. Executar Regressão e Plotar Forest
    # Nota: A função executar_regressao_multinomial do script original já retorna o DF de resultados
    df_reg_results = executar_regressao_multinomial(df_final)
    if df_reg_results is not None:
        plot_forest(df_reg_results)
    else:
        print("Regressão não executada (statsmodels ausente ou erro nos dados).")

if __name__ == "__main__":
    main()
