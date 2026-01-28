import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

try:
    import pymannkendall as mk
except ImportError:
    mk = None
    print("[AVISO] Biblioteca 'pymannkendall' não encontrada. O teste de Mann-Kendall será pulado.")

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
CORES_RACA = {
    'Branca/Amarela': '#31859C', # Azul Petróleo
    'Preta': '#8064A2',          # Roxo
    'Parda': '#C0504D',          # Vermelho Tijolo
    'Indígena': '#F79646',       # Laranja
    'Ignorada/Não informada': '#7F7F7F' # Cinza
}

# =============================================================================
# FUNÇÕES DE HARMONIZAÇÃO
# =============================================================================

def harmonizar_raca_pvha(df_pvha):
    """
    Cria a coluna 'raca4_cat' no DataFrame PVHA baseada em 'Raca_cat',
    para ficar compatível com a base de PrEP.
    """
    if 'Raca_cat' not in df_pvha.columns:
        print("   [AVISO] Coluna 'Raca_cat' não encontrada em PVHA.")
        return df_pvha

    def _map_raca(val):
        if pd.isna(val) or str(val).lower() in ['none', 'nan', 'ignorado']:
            return 'Ignorada/Não informada'
        
        val_clean = str(val).strip()
        if val_clean in ['Branca', 'Amarela']:
            return 'Branca/Amarela'
        elif val_clean == 'Parda':
            return 'Parda'
        elif val_clean == 'Preta':
            return 'Preta'
        elif val_clean == 'Indígena':
            return 'Indígena'
        else:
            return 'Ignorada/Não informada'

    df_pvha['raca4_cat'] = df_pvha['Raca_cat'].apply(_map_raca)
    return df_pvha

# =============================================================================
# CÁLCULO
# =============================================================================

def calcular_indicador_raca(df_prep_ativos, df_pvha_novos):
    """
    Calcula o indicador PrEP agrupado por Raça/Cor.
    Retorna DataFrame com Numerador, Denominador e Indicador.
    """
    print("\n   Calculando indicador por Raça/Cor...")
    
    # 1. Numerador (PrEP)
    # Assumindo que raca4_cat já existe no df_prep
    num_raca = df_prep_ativos['raca4_cat'].value_counts()
    
    # 2. Denominador (PVHA)
    # Precisamos harmonizar antes, caso não tenha sido feito fora
    if 'raca4_cat' not in df_pvha_novos.columns:
        df_pvha_novos = harmonizar_raca_pvha(df_pvha_novos.copy())
    
    den_raca = df_pvha_novos['raca4_cat'].value_counts()
    
    # 3. Juntar
    df_ind = pd.DataFrame({'Em PrEP': num_raca, 'Novos Vinculados': den_raca})
    df_ind = df_ind.fillna(0).astype(int)
    
    # 4. Calcular Indicador
    df_ind['Indicador'] = df_ind.apply(
        lambda x: round(x['Em PrEP'] / x['Novos Vinculados'], 2) if x['Novos Vinculados'] > 0 else 0, 
        axis=1
    )
    
    # Ordenar
    ordem_padrao = ['Branca/Amarela', 'Preta', 'Parda', 'Indígena', 'Ignorada/Não informada']
    df_ind = df_ind.reindex([x for x in ordem_padrao if x in df_ind.index])
    
    return df_ind

# =============================================================================
# VISUALIZAÇÃO
# =============================================================================

def gerar_grafico_raca(df_ind, output_folder):
    """
    Gera gráfico de barras para o indicador por raça.
    """
    print("   Gerando gráfico por Raça...")
    output_dir = os.path.join(output_folder, "Graficos_Sociodemograficos")
    os.makedirs(output_dir, exist_ok=True)
    
    # Remover 'Ignorada' do gráfico se o usuário preferir, ou manter para transparência.
    # Vamos manter, mas talvez com cor cinza discreta.
    
    dados = df_ind['Indicador']
    cores = [CORES_RACA.get(idx, '#333333') for idx in dados.index]
    
    try:
        plt.figure(figsize=(10, 6))
        
        bars = plt.bar(dados.index, dados.values, color=cores, edgecolor='black', alpha=0.8)
        
        # Labels nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                     f'{height:.2f}',
                     ha='center', va='bottom', fontweight='bold')

        # Estilo
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.title('Indicador PrEP:HIV por Raça/Cor')
        plt.ylabel('Razão (PrEP / Novos Vinculados)')
        
        path_img = os.path.join(output_dir, "indicador_raca.png")
        plt.savefig(path_img, dpi=150)
        plt.close()
        print(f"   Gráfico salvo: {path_img}")
        
    except Exception as e:
        print(f"   Erro ao gerar gráfico de raça: {e}")

def gerar_grafico_serie_raca(df_serie, output_folder):
    """
    Gera gráfico de linhas da série histórica por raça.
    df_serie: DataFrame com index=Raca e colunas=Meses
    """
    print("   Gerando gráfico de Série Histórica por Raça...")
    output_dir = os.path.join(output_folder, "Graficos_Sociodemograficos")
    os.makedirs(output_dir, exist_ok=True)
    
    # Preparar dados para plot
    x_numeric = np.arange(len(df_serie.columns))
    x_labels = [str(c) for c in df_serie.columns]
    
    try:
        plt.figure(figsize=(12, 8))
        
        for raca in df_serie.index:
            if raca == 'Ignorada/Não informada':
                cor = '#7f7f7f'
                estilo = '--' # Tracejado para ignorados
                alpha = 0.6
            else:
                cor = CORES_RACA.get(raca, '#333333')
                estilo = '-'
                alpha = 1.0
                
            dados = df_serie.loc[raca]
            plt.plot(x_numeric, dados.values, label=raca, color=cor, linestyle=estilo, alpha=alpha, linewidth=2)

        # Estilo
        plt.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")
        plt.xticks(x_numeric[::6], [x_labels[idx] for idx in x_numeric[::6]], rotation=45)
        
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fancybox=True)
        plt.title('Série Histórica do Indicador PrEP:HIV por Raça/Cor')
        plt.ylabel('Razão (PrEP / Novos Vinculados)')
        plt.tight_layout()
        
        path_img = os.path.join(output_dir, "serie_historica_raca.png")
        plt.savefig(path_img, dpi=150)
        plt.close()
        print(f"   Gráfico salvo: {path_img}")
        
    except Exception as e:
        print(f"   Erro ao gerar gráfico de série raça: {e}")

def calcular_mann_kendall_raca(df_serie_hist, n_meses=12):
    """
    Calcula o teste de Mann-Kendall para cada categoria de raça nos últimos n meses.
    """
    if mk is None:
        return pd.DataFrame()
        
    print(f"   Calculando Mann-Kendall Raça (últimos {n_meses} meses)...")
    lista_resultados = []
    
    try:
        for raca in df_serie_hist.index:
            # Pegar últimos n meses
            dados_recentes = df_serie_hist.loc[raca].tail(n_meses)
            valores = dados_recentes.values.astype(float)
            
            resultado = mk.original_test(valores)
            
            lista_resultados.append({
                "Raça/Cor": raca,
                "Tendência": resultado.trend,
                "p-value": round(resultado.p, 4),
                "Tau": round(resultado.Tau, 4),
                "Inclinação (Slope)": round(resultado.slope, 4),
                "Significativo": "Sim" if resultado.p < 0.05 else "Não"
            })
            
        return pd.DataFrame(lista_resultados)
        
    except Exception as e:
        print(f"   Erro ao calcular Mann-Kendall Raça: {e}")
        return pd.DataFrame()
