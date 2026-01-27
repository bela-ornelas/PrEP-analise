import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
import numpy as np

# Adiciona diretório atual ao path
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

def plot_forest_robust(df_reg_results):
    if df_reg_results is None or df_reg_results.empty:
        print("Sem dados de regressão para plotar.")
        return

    print("Gerando Forest Plots...")
    
    # Garantir que diretório de saída existe
    output_dir = "graficos_forest"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    outcomes = df_reg_results['Outcome'].unique()
    
    for outcome in outcomes:
        print(f"  - Processando desfecho: {outcome}")
        data = df_reg_results[df_reg_results['Outcome'] == outcome].copy()
        
        # Filtrar Intercepto
        data = data[~data['Variable_Clean'].str.contains('Intercept')]
        
        # Inverter ordem para plotar de cima para baixo
        data = data.iloc[::-1].reset_index(drop=True)
        
        # Configurar Figura
        height = max(6, len(data) * 0.4)
        fig, ax = plt.subplots(figsize=(10, height))
        
        # Linha de referência
        ax.axvline(x=1, color='black', linestyle='--', linewidth=1, alpha=0.7)
        
        # Plotar cada ponto individualmente para controle total de cores
        y_positions = range(len(data))
        
        for i, row in data.iterrows():
            y = i
            aor = row['aOR']
            lower = row['CI_Lower']
            upper = row['CI_Upper']
            pval = row['p_value']
            
            # Cor: Vermelho se p < 0.05, Cinza caso contrário
            color = '#e74c3c' if pval < 0.05 else '#95a5a6'
            
            # Barra de Erro
            ax.plot([lower, upper], [y, y], color=color, linewidth=1.5, zorder=1)
            
            # Ponto (aOR)
            ax.scatter(aor, y, color=color, s=40, zorder=2)
            
            # Adicionar texto com o valor do aOR e IC à direita
            text_label = f"{aor:.2f} ({lower:.2f}-{upper:.2f})"
            if pval < 0.05:
                text_label += "*"
                font_weight = 'bold'
            else:
                font_weight = 'normal'
                
            # Calcular posição do texto (um pouco à direita do limite superior, mas com limite)
            # Para evitar que fique muito longe em escalas log
            text_x = upper * 1.1 if upper < 10 else upper + 0.5
            
            # Ajuste fino se a escala for log, o posicionamento visual muda
            # Vamos plotar o texto na margem direita do gráfico usando transformação de eixos se preferir,
            # mas manter junto à barra é mais clássico de Forest Plot.
            
        # Configurar Eixos
        ax.set_yticks(y_positions)
        ax.set_yticklabels(data['Variable_Clean'], fontsize=10)
        
        ax.set_xlabel('Adjusted Odds Ratio (log scale)', fontsize=11)
        ax.set_title(f'Multinomial Regression: {outcome}\nRef: Sustained Use', fontsize=13, fontweight='bold')
        
        # Escala Logarítmica para OR é o padrão
        ax.set_xscale('log')
        
        # Definir limites X razoáveis
        # Mínimo: um pouco abaixo do menor IC inferior
        # Máximo: um pouco acima do maior IC superior
        x_min = max(0.1, data['CI_Lower'].min() * 0.8)
        x_max = min(20, data['CI_Upper'].max() * 1.2) # Trava em 20 para evitar outliers extremos esticarem demais
        
        ax.set_xlim(x_min, x_max)
        
        # Grid auxiliar
        ax.grid(axis='x', which='major', linestyle='--', alpha=0.4)
        ax.grid(axis='x', which='minor', linestyle=':', alpha=0.2)
        
        # Remover bordas desnecessárias
        sns.despine(left=True, bottom=False)
        
        plt.tight_layout()
        
        safe_name = outcome.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '')
        filename = os.path.join(output_dir, f'forest_plot_{safe_name}.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"    Salvo: {filename}")
        plt.close()

def main():
    DATA_FECHAMENTO = '2025-12-31'
    
    print(">>> 1. Carregando dados...")
    try:
        bases = carregar_bases(pd.to_datetime(DATA_FECHAMENTO).date(), use_cache=True)
        df_disp = bases.get("Disp", pd.DataFrame())
        df_cad_prep = bases.get("Cadastro_PrEP", pd.DataFrame())
    except Exception as e:
        print(f"Erro ao carregar bases: {e}")
        return
    
    print(">>> 2. Processando dados...")
    df_disp, df_disp_semdupl = clean_disp_df(df_disp, DATA_FECHAMENTO)
    df_cad_prep = process_cadastro(df_cad_prep)
    df_disp_semdupl = enrich_disp_data(df_disp_semdupl, df_cad_prep, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    
    try:
        df_cad_prep = calculate_population_groups(df_cad_prep)
    except: pass
    
    df_classificacao = classificar_comportamento(df_disp_semdupl, DATA_FECHAMENTO)
    df_final = df_classificacao.merge(df_cad_prep, on='codigo_pac_eleito', how='left')
    
    # Recalcular Faixa Etária
    hoje = pd.to_datetime(DATA_FECHAMENTO)
    if 'data_nascimento' in df_final.columns:
        df_final['data_nascimento'] = pd.to_datetime(df_final['data_nascimento'], errors='coerce')
        df_final['idade'] = (hoje - df_final['data_nascimento']) / pd.to_timedelta(365.25, unit='D')
        bins = [0, 18, 24, 29, 39, 49, 100]
        labels = ['<18', '18-24', '25-29', '30-39', '40-49', '50+']
        df_final['faixa_etaria'] = pd.cut(df_final['idade'], bins=bins, labels=labels)

    # 3. Executar Regressão
    print(">>> 3. Executando Regressão...")
    df_reg_results = executar_regressao_multinomial(df_final)
    
    # 4. Plotar
    if df_reg_results is not None:
        plot_forest_robust(df_reg_results)
    else:
        print("Não foi possível gerar os gráficos pois a regressão falhou.")

if __name__ == "__main__":
    main()
