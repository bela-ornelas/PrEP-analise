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
    num_raca = df_prep_ativos['raca4_cat'].value_counts()
    
    # 2. Denominador (PVHA)
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
    
    dados = df_ind['Indicador']
    cores = [CORES_RACA.get(idx, '#333333') for idx in dados.index]
    
    try:
        plt.figure(figsize=(10, 6))
        bars = plt.bar(dados.index, dados.values, color=cores, edgecolor='black', alpha=0.8)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                     f'{height:.2f}',
                     ha='center', va='bottom', fontweight='bold')

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

def gerar_grafico_serie_raca(df_serie, output_folder, df_mk_resultados=None):
    """
    Gera gráfico de linhas da série histórica por raça com marcadores e títulos dinâmicos.
    """
    print("   Gerando gráfico de Série Histórica por Raça...")
    output_dir = os.path.join(output_folder, "Graficos_Sociodemograficos")
    os.makedirs(output_dir, exist_ok=True)
    
    dict_tendencias = {}
    if df_mk_resultados is not None and not df_mk_resultados.empty:
        for _, row in df_mk_resultados.iterrows():
            raca = row.get('Raça/Cor', row.get('Local', ''))
            trend = row.get('Tendência', '')
            sig = row.get('Significativo', '')
            
            icone = "-"
            if trend == 'increasing': icone = "▲"
            elif trend == 'decreasing': icone = "▼"
            if sig == "Não": icone = "-"
            dict_tendencias[raca] = icone

    x_numeric = np.arange(len(df_serie.columns))
    x_labels = [str(c) for c in df_serie.columns]
    
    try:
        plt.figure(figsize=(12, 8))
        
        col_ini = df_serie.columns[0]
        col_fim = df_serie.columns[-1]
        
        def fmt_titulo(c):
            m, y = str(c).split('_')
            meses = {1:'jan', 2:'fev', 3:'mar', 4:'abr', 5:'mai', 6:'jun', 
                     7:'jul', 8:'ago', 9:'set', 10:'out', 11:'nov', 12:'dez'}
            return f"{meses[int(m)]}/{y}"
            
        titulo_periodo = f"{fmt_titulo(col_ini)} a {fmt_titulo(col_fim)}"
        
        if not df_serie.empty:
            df_serie = df_serie.sort_values(by=col_fim, ascending=False)
        
        count_raca = 0
        for raca in df_serie.index:
            if raca == 'Ignorada/Não informada':
                cor = '#7F7F7F' 
                estilo = '--'
                alpha = 0.6
            else:
                cor = CORES_RACA.get(raca, '#333333')
                estilo = '-'
                alpha = 1.0
            
            label_final = raca
            if raca in dict_tendencias:
                label_final = f"{raca} ({dict_tendencias[raca]})"
                
            dados = df_serie.loc[raca]
            plt.plot(x_numeric, dados.values, label=label_final, color=cor, linestyle=estilo, alpha=alpha, linewidth=2)
            
            # Marcadores e Labels (Início e Fim)
            indices_pontos = [0, len(dados) - 1]
            for idx_ponto in indices_pontos:
                val = dados.values[idx_ponto]
                plt.scatter(x_numeric[idx_ponto], val, color=cor, zorder=5)
                
                # Alternar posição do label
                # Se for o início (idx_ponto == 0), sempre bottom.
                # Se for o fim, alterna baseado no índice da raça (count_raca)
                offset = 0.05
                va = 'bottom'
                
                if idx_ponto > 0: # Ponto final
                    if count_raca % 2 == 0:
                        va = 'bottom'
                        offset = 0.08
                    else:
                        va = 'top'
                        offset = -0.08
                
                plt.text(x_numeric[idx_ponto], val + offset, f"{val:.2f}".replace('.', ','), 
                         color=cor, fontsize=9, fontweight='bold', ha='center', va=va)
            
            count_raca += 1

        # Estilo
        plt.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")
        
        # Formatar todos os labels do eixo X para jan/2022 etc.
        x_labels_fmt = [fmt_titulo(c) for c in x_labels]
        
        # Aplicar Ticks horizontais (rotation=0)
        plt.xticks(x_numeric[::6], [x_labels_fmt[idx] for idx in x_numeric[::6]], rotation=0)
        
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # --- NOVO LAYOUT DE LEGENDAS (INFERIOR - REVERTIDO PARA VERSÃO PREFERIDA) ---
        
        # Legenda Principal: Logo abaixo do eixo X
        # Legenda Principal: Coordenadas de Figura (0.05 = logo acima do rodapé que ocupa ~0.04)
        leg = plt.legend(bbox_to_anchor=(0.5, 0.05), loc='lower center', 
                         bbox_transform=plt.gcf().transFigure,
                         fancybox=True, title="Raça/cor (tendência)", ncol=3, 
                         fontsize=9, borderpad=0.3, labelspacing=0.3)
        
        # Legenda Explicativa: Rodapé absoluto da figura
        texto_explicativo = "Tendência (Mann-Kendall): ▲ Aumento  |  ▼ Queda  |  - Sem tendência"
        
        plt.gcf().text(0.5, 0.01, texto_explicativo, fontsize=9, ha='center', va='bottom',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.5, pad=0.3))

        plt.title(f'Série histórica do indicador PrEP:HIV por raça/cor. Brasil, {titulo_periodo}')
        plt.ylabel('Razão (PrEP / Novos Vinculados)')
        
        # Margem inferior ajustada para 13% (Gráfico expandido perto da legenda)
        plt.tight_layout(rect=[0, 0.13, 1, 1])
        
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

def gerar_graficos_regionais_raca(dict_series, output_folder, dict_mk=None):
    """
    Gera múltiplos gráficos de série histórica por raça, um para cada região/corte.
    dict_series: { 'Brasil': df, 'Norte': df, ... }
    dict_mk: { 'Brasil': df_mk, 'Norte': df_mk, ... } (Opcional)
    """
    print("   Gerando gráficos de Raça por Região...")
    
    for nome_regiao, df_serie in dict_series.items():
        # Filtrar MK correspondente se existir
        df_mk = None
        if dict_mk and nome_regiao in dict_mk:
            df_mk = dict_mk[nome_regiao]
            
        print(f"      Processando: {nome_regiao}")
        
        # Reutilizar a função de plotagem, mas ajustando o nome do arquivo e título
        # A função original salva como 'serie_historica_raca.png'.
        # Vamos ter que adaptar a função original ou criar uma interna.
        # Melhor adaptar a original para aceitar sufixo ou nome de arquivo.
        
        _plotar_serie_raca_custom(df_serie, output_folder, df_mk, nome_regiao)

def _plotar_serie_raca_custom(df_serie, output_folder, df_mk, nome_regiao, serie_total_regional=None):
    """Versão interna adaptada da plotagem para regionalização com linha de benchmark."""
    output_dir = os.path.join(output_folder, "Graficos_Sociodemograficos")
    os.makedirs(output_dir, exist_ok=True)
    
    dict_tendencias = {}
    if df_mk is not None and not df_mk.empty:
        for _, row in df_mk.iterrows():
            raca = row.get('Raça/Cor', row.get('Local', ''))
            trend = row.get('Tendência', '')
            sig = row.get('Significativo', '')
            icone = "-"
            if trend == 'increasing': icone = "▲"
            elif trend == 'decreasing': icone = "▼"
            if sig == "Não": icone = "-"
            dict_tendencias[raca] = icone

    x_numeric = np.arange(len(df_serie.columns))
    x_labels = [str(c) for c in df_serie.columns]
    x_labels_fmt = []
    
    # Função de formatação de data para labels
    def fmt_label(c):
        try:
            m, y = str(c).split('_')
            meses = {1:'jan', 2:'fev', 3:'mar', 4:'abr', 5:'mai', 6:'jun', 
                     7:'jul', 8:'ago', 9:'set', 10:'out', 11:'nov', 12:'dez'}
            return f"{meses[int(m)]}/{y}"
        except: return str(c)

    x_labels_fmt = [fmt_label(c) for c in df_serie.columns]
    
    try:
        plt.figure(figsize=(12, 8))
        
        # Título do Período
        titulo_periodo = f"{x_labels_fmt[0]} a {x_labels_fmt[-1]}"
        
        # Ordenar (decrescente pelo último mês)
        if not df_serie.empty:
            col_fim = df_serie.columns[-1]
            df_serie = df_serie.sort_values(by=col_fim, ascending=False)
        
        # 1. Plotar Categorias de Raça (Exceto Ignorada)
        for raca in df_serie.index:
            if 'ignora' in raca.lower() or 'não informa' in raca.lower():
                continue
                
            cor = CORES_RACA.get(raca, '#333333')
            label_final = f"{raca} ({dict_tendencias.get(raca, '-')})"
            dados = df_serie.loc[raca]
            
            plt.plot(x_numeric, dados.values, label=label_final, color=cor, linewidth=2.5, zorder=3)
            
            # Marcadores Início/Fim
            for idx in [0, len(dados)-1]:
                val = dados.values[idx]
                plt.scatter(x_numeric[idx], val, color=cor, zorder=5)
                plt.text(x_numeric[idx], val + 0.05, f"{val:.2f}".replace('.', ','), 
                         color=cor, fontsize=9, fontweight='bold', ha='center', va='bottom')

        # 2. Plotar Linha Tracejada do TOTAL REGIONAL
        if serie_total_regional is not None:
            plt.plot(x_numeric, serie_total_regional.values, 
                     label=f"Total {nome_regiao}", color='black', 
                     linestyle='--', linewidth=3, zorder=2, alpha=0.8)
            
            # Marcador Final do Total
            last_val = serie_total_regional.values[-1]
            plt.text(x_numeric[-1], last_val - 0.15, f"{last_val:.2f}".replace('.', ','), 
                     color='black', fontsize=10, fontweight='bold', ha='center', va='top')

        # Estilo
        plt.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")
        plt.xticks(x_numeric[::6], [x_labels_fmt[idx] for idx in x_numeric[::6]], rotation=0)
        
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Legendas
        plt.legend(bbox_to_anchor=(0.5, 0.05), loc='lower center', 
                         bbox_transform=plt.gcf().transFigure,
                         fancybox=True, title="Raça/cor (tendência)", ncol=3, fontsize=9)
        
        texto_explicativo = "Tendência (Mann-Kendall): ▲ Aumento  |  ▼ Queda  |  - Sem tendência"
        plt.gcf().text(0.5, 0.01, texto_explicativo, fontsize=9, ha='center', va='bottom',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.5, pad=0.3))

        local_titulo = "Brasil" if nome_regiao == "Brasil" else f"Região {nome_regiao}"
        plt.title(f'Série histórica do indicador PrEP:HIV por raça/cor. {local_titulo}, {titulo_periodo}')
        plt.ylabel('Razão (PrEP / Novos Vinculados)')
        
        plt.tight_layout(rect=[0, 0.13, 1, 1])
        
        nome_clean = nome_regiao.replace(' ', '_').replace('/', '-')
        path_img = os.path.join(output_dir, f"serie_historica_raca_{nome_clean}.png")
        plt.savefig(path_img, dpi=150)
        print(f"      Gráfico salvo: {path_img}")

        if nome_regiao == 'Brasil':
            path_legacy = os.path.join(output_dir, "serie_historica_raca.png")
            plt.savefig(path_legacy, dpi=150)
            print(f"      Gráfico salvo (legado): {path_legacy}")
        
        plt.close()
    except Exception as e:
        print(f"      Erro ao gerar gráfico {nome_regiao}: {e}")

def gerar_graficos_regionais_raca(dict_series, output_folder, dict_mk=None, dict_totais=None):
    """
    Gera múltiplos gráficos de série histórica por raça.
    dict_totais: { 'Norte': Series_Total, ... }
    """
    print("   Gerando gráficos de Raça por Região...")
    for nome_regiao, df_serie in dict_series.items():
        df_mk = dict_mk.get(nome_regiao) if dict_mk else None
        serie_total = dict_totais.get(nome_regiao) if dict_totais else None
        
        print(f"      Processando: {nome_regiao}")
        _plotar_serie_raca_custom(df_serie, output_folder, df_mk, nome_regiao, serie_total)