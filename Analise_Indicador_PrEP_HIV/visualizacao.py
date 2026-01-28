import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

try:
    import pymannkendall as mk
except ImportError:
    mk = None
    print("[AVISO] Biblioteca 'pymannkendall' não encontrada. O teste de Mann-Kendall será pulado.")

# =============================================================================
# CORES E ESTILOS
# =============================================================================
CORES_BASE = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

def _configurar_plot():
    """Configuração padrão para gráficos (grid, spines, etc)."""
    plt.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)

# =============================================================================
# GRÁFICOS
# =============================================================================

def gerar_grafico_brasil(indicador_brasil, base_output_dir):
    """
    Gera gráfico de linha do indicador Brasil (Mensal).
    Eixo X: todos os meses plotados, mas labels apenas para Jan e Jul.
    """
    print("\n--- GERANDO GRÁFICO BRASIL ---")
    
    output_dir = os.path.join(base_output_dir, "Graficos")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Prepara os labels e valores
        datas = [f"{col.split('_')[1]}-{col.split('_')[0].zfill(2)}" for col in indicador_brasil.index]
        combined = sorted(zip(datas, indicador_brasil.values), key=lambda x: x[0])
        datas_ordenadas, valores_ordenados = zip(*combined)

        def formatar_data(data_str):
            ano, mes = data_str.split('-')
            if mes == '01': return f"jan/{ano}"
            elif mes == '07': return f"jul/{ano}"
            else: return f"{mes}/{ano}"

        labels_formatados = [formatar_data(d) for d in datas_ordenadas]
        indices_marcas = [i for i, d in enumerate(datas_ordenadas) if d.split('-')[1] in ['01', '07']]

        plt.figure(figsize=(10, 5))
        plt.plot(datas_ordenadas, valores_ordenados, color='#1f77b4', linewidth=2)
        
        plt.scatter([datas_ordenadas[i] for i in indices_marcas],
                    [valores_ordenados[i] for i in indices_marcas],
                    color='darkblue', zorder=5, label='Jan/Jul')

        for i in indices_marcas:
            val = valores_ordenados[i]
            plt.text(datas_ordenadas[i], val + 0.05,
                     f"{val:.2f}".replace('.', ','), 
                     ha='center', va='bottom', fontsize=9, fontweight='bold')

        plt.ylabel('Indicador PrEP:HIV')
        plt.title('Indicador PrEP:HIV mensal - Brasil')
        
        plt.xticks([datas_ordenadas[i] for i in indices_marcas], 
                   [labels_formatados[i] for i in indices_marcas], rotation=0)

        max_val = max(valores_ordenados) if valores_ordenados else 1
        plt.ylim(0, max_val * 1.15)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        
        path_img = os.path.join(output_dir, "grafico_BR.png")
        plt.savefig(path_img, dpi=150)
        plt.close()
        print(f"   Gráfico salvo: {path_img}")
        
    except Exception as e:
        print(f"   Erro ao gerar gráfico Brasil: {e}")

def gerar_analise_regioes(graf, base_output_dir):
    """
    Gera gráficos comparativos por Região e Brasil, linhas de tendência e teste Mann-Kendall.
    """
    print("\n--- GERANDO GRÁFICOS REGIONAIS ---")
    output_dir = os.path.join(base_output_dir, "Graficos")
    os.makedirs(output_dir, exist_ok=True)
    
    cores = CORES_BASE * 3
    
    # --- GRÁFICO 1: SÉRIE HISTÓRICA ---
    try:
        plt.figure(figsize=(12, 6))
        i = len(graf) - 1
        for grupo in graf.index:
            dados = graf.loc[grupo]
            plt.plot(dados.index, dados.values, label=grupo, color=cores[i % len(cores)])
            i = i - 1

        _configurar_plot()
        x_ticks = list(graf.columns)[::6]
        plt.xticks(x_ticks, rotation=45)
        plt.legend(bbox_to_anchor=(1, 0.8), fancybox=True, reverse=True)
        plt.title('Série Histórica - Regiões e Brasil')
        plt.tight_layout()
        
        path_img1 = os.path.join(output_dir, "serie_historica_regioes.png")
        plt.savefig(path_img1)
        plt.close()
        print(f"   Gráfico salvo: {path_img1}")
    except Exception as e:
        print(f"   Erro ao gerar Gráfico Histórico Regiões: {e}")

    # --- GRÁFICO 2: TENDÊNCIA 18 MESES ---
    n = 18
    try:
        plt.figure(figsize=(12, 6))
        i = len(graf) - 1
        
        for grupo_tend in graf.index:
            dados_recentes = graf.loc[grupo_tend].tail(n)
            x = np.arange(len(dados_recentes)).reshape(-1, 1)
            y = dados_recentes.values.reshape(-1, 1)
            
            modelo = LinearRegression().fit(x, y)
            y_pred = modelo.predict(x)
            
            cor_atual = cores[i % len(cores)]
            inclinacao = modelo.coef_[0][0]
            r2 = r2_score(y, y_pred)
            
            plt.plot(dados_recentes.index, y_pred.flatten(), linestyle='--', 
                     label=f'Tendência ({grupo_tend})', color=cor_atual)
            
            plt.annotate(f'{grupo_tend} \u03B1 = {inclinacao:.2f} R²: {r2:.2f} ',
                         xy=(dados_recentes.index[-1], y_pred.flatten()[-1]), 
                         xytext=(5, -5), textcoords='offset points', fontsize=8)
            i = i - 1

        for grupo in graf.index:
            dados = graf.loc[grupo].tail(n)
            plt.plot(dados.index, dados.values, label=grupo, alpha=0.3, linewidth=1)

        _configurar_plot()
        x_ticks = list(graf.columns)[-n:][::3]
        plt.xticks(x_ticks, rotation=45)
        plt.title(f'Linhas de Tendência - Últimos {n} Meses')
        plt.tight_layout()
        
        path_img2 = os.path.join(output_dir, "tendencia_18m_regioes.png")
        plt.savefig(path_img2)
        plt.close()
        print(f"   Gráfico salvo: {path_img2}")

    except Exception as e:
        print(f"   Erro ao gerar Gráfico Tendência Regiões: {e}")

    return _calcular_mann_kendall(graf, n)

def gerar_analise_uf(graf, base_output_dir, map_siglas=None):
    """
    Gera gráficos e análises para UFs (Série Histórica, Tendência 12m, Mann-Kendall).
    """
    print("\n--- GERANDO GRÁFICOS POR UF ---")
    if graf.empty:
        print("   [ERRO] DataFrame de UFs está vazio. Pulando análise.")
        return pd.DataFrame()
        
    output_dir = os.path.join(base_output_dir, "Graficos")
    if map_siglas is None: map_siglas = {}
    
    cores = CORES_BASE * 4 
    x_numeric = np.arange(len(graf.columns))
    x_labels = [str(c) for c in graf.columns]
    
    # --- GRÁFICO 1: SÉRIE HISTÓRICA UF ---
    try:
        plt.figure(figsize=(12, 8)) 
        i = len(graf) - 1
        for grupo in graf.index:
            dados = graf.loc[grupo]
            label_plot = map_siglas.get(str(grupo), str(grupo))
            plt.plot(x_numeric, dados.values, label=label_plot, color=cores[i % len(cores)])
            i = i - 1

        _configurar_plot()
        plt.xticks(x_numeric[::6], [x_labels[idx] for idx in x_numeric[::6]], rotation=45)
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', ncol=2, fancybox=True)
        plt.title('Série Histórica - Unidades Federativas (UF)')
        plt.tight_layout()
        
        path_img1 = os.path.join(output_dir, "serie_historica_UF.png")
        plt.savefig(path_img1)
        plt.close()
        print(f"   Gráfico salvo: {path_img1}")
    except Exception as e:
        print(f"   Erro ao gerar Gráfico Histórico UF: {e}")

    # --- GRÁFICO 2: TENDÊNCIA 12 MESES ---
    n = 12
    try:
        plt.figure(figsize=(12, 8))
        i = len(graf) - 1
        
        x_numeric_rec = np.arange(n)
        x_labels_rec = x_labels[-n:]
        
        for grupo_tend in graf.index:
            dados_recentes = graf.loc[grupo_tend].tail(n)
            
            x_reg = x_numeric_rec.reshape(-1, 1)
            y_reg = dados_recentes.values.reshape(-1, 1)
            
            modelo = LinearRegression().fit(x_reg, y_reg)
            y_pred = modelo.predict(x_reg)
            
            cor_atual = cores[i % len(cores)]
            label_plot = map_siglas.get(str(grupo_tend), str(grupo_tend))
            
            plt.plot(x_numeric_rec, y_pred.flatten(), linestyle='--', label=f'{label_plot}', color=cor_atual)
            i = i - 1

        _configurar_plot()
        plt.xticks(x_numeric_rec[::2], [x_labels_rec[idx] for idx in x_numeric_rec[::2]], rotation=45)
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', ncol=2, title="Tendências")
        plt.title(f'Linhas de Tendência por UF - Últimos {n} Meses')
        plt.tight_layout()
        
        path_img2 = os.path.join(output_dir, "tendencia_12m_UF.png")
        plt.savefig(path_img2)
        plt.close()
        print(f"   Gráfico salvo: {path_img2}")
    except Exception as e:
        print(f"   Erro ao gerar Gráfico Tendência UF: {e}")

    # Mann Kendall com nome customizado (Code - Sigla)
    def custom_name_formatter(name):
        sigla = map_siglas.get(str(name), "")
        return f"{name} - {sigla}" if sigla else str(name)

    return _calcular_mann_kendall(graf, n, name_formatter=custom_name_formatter)

def gerar_analise_aha(graf, output_folder):
    """
    Gera gráficos e análises para o grupo AHA (Capitais + Brasil).
    """
    print("\n--- GERANDO GRÁFICOS AHA ---")
    output_dir = os.path.join(output_folder, "Graficos")
    os.makedirs(output_dir, exist_ok=True)
    
    cores = CORES_BASE * 2
    x_numeric = np.arange(len(graf.columns))
    x_labels = [str(c) for c in graf.columns]
    
    # --- GRÁFICO 1: SÉRIE HISTÓRICA AHA ---
    try:
        plt.figure(figsize=(12, 8)) 
        i = len(graf) - 1
        
        for grupo in graf.index:
            dados = graf.loc[grupo]
            label_nome = str(grupo)
            
            # Estilo customizado para Brasil
            if label_nome == 'Brasil':
                cor = 'black'
                estilo = '--'
                largura = 3.0
                z_order = 10
            else:
                cor = cores[i % len(cores)]
                estilo = '-'
                largura = 2.0
                z_order = 5
                i = i - 1 # Só decrementa cor para capitais
            
            plt.plot(x_numeric, dados.values, label=label_nome, color=cor, 
                     linestyle=estilo, linewidth=largura, zorder=z_order)
            
            # Marcadores e Rótulos (Início e Fim)
            indices_pontos = [0, len(dados) - 1]
            for idx in indices_pontos:
                val = dados.values[idx]
                # Scatter no ponto
                plt.scatter(x_numeric[idx], val, color=cor, zorder=z_order+1, s=30)
                
                # Texto do valor
                # Ajuste fino: Se for Brasil, negrito e maior
                weight = 'bold' if label_nome == 'Brasil' else 'normal'
                fontsize = 10 if label_nome == 'Brasil' else 9
                
                plt.text(x_numeric[idx], val + 0.05, f"{val:.2f}".replace('.', ','), 
                         color=cor, fontsize=fontsize, fontweight=weight, ha='center', va='bottom')

        # Formatar datas do eixo X
        def formatar_data(data_str):
            try:
                m, y = str(data_str).split('_')
                if m == '1': return f"jan/{y}"
                elif m == '7': return f"jul/{y}"
                else: return f"{m}/{y}"
            except: return str(data_str)

        x_labels_fmt = [formatar_data(d) for d in x_labels]

        _configurar_plot()
        plt.xticks(x_numeric[::6], [x_labels_fmt[idx] for idx in x_numeric[::6]], rotation=45)
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fancybox=True)
        plt.title('Série Histórica - AHA (Capitais Selecionadas + Brasil)')
        plt.tight_layout()
        
        path_img1 = os.path.join(output_dir, "serie_historica_AHA.png")
        plt.savefig(path_img1)
        plt.close()
        print(f"   Gráfico salvo: {path_img1}")
    except Exception as e:
        print(f"   Erro ao gerar Gráfico Histórico AHA: {e}")

    # --- GRÁFICO 2: TENDÊNCIA AHA (12 meses) ---
    n = 12
    try:
        plt.figure(figsize=(12, 8))
        i = len(graf) - 1
        
        x_numeric_rec = np.arange(n)
        x_labels_rec = x_labels[-n:]
        
        for grupo_tend in graf.index:
            dados_recentes = graf.loc[grupo_tend].tail(n)
            
            x_reg = x_numeric_rec.reshape(-1, 1)
            y_reg = dados_recentes.values.reshape(-1, 1)
            
            modelo = LinearRegression().fit(x_reg, y_reg)
            y_pred = modelo.predict(x_reg)
            
            cor_atual = cores[i % len(cores)]
            plt.plot(x_numeric_rec, y_pred.flatten(), linestyle='--', label=f'{grupo_tend}', color=cor_atual, linewidth=2)
            i = i - 1

        _configurar_plot()
        plt.xticks(x_numeric_rec[::2], [x_labels_rec[idx] for idx in x_numeric_rec[::2]], rotation=45)
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', title="Tendências")
        plt.title(f'Linhas de Tendência AHA - Últimos {n} Meses')
        plt.tight_layout()
        
        path_img2 = os.path.join(output_dir, "tendencia_12m_AHA.png")
        plt.savefig(path_img2)
        plt.close()
        print(f"   Gráfico salvo: {path_img2}")
    except Exception as e:
        print(f"   Erro ao gerar Gráfico Tendência AHA: {e}")

    return _calcular_mann_kendall(graf, n)

def _calcular_mann_kendall(graf, n, name_formatter=None):
    """Função auxiliar interna para teste Mann-Kendall."""
    df_mk_result = pd.DataFrame()
    if mk:
        print(f"   Calculando Mann-Kendall (últimos {n} meses)...")
        lista_resultados = []
        try:
            for grupo_test in graf.index:
                dados_test = graf.loc[grupo_test].tail(n)
                valores = dados_test.values.astype(float) # Garantir float
                
                resultado = mk.original_test(valores)
                
                nome_final = str(grupo_test)
                if name_formatter:
                    nome_final = name_formatter(grupo_test)
                
                lista_resultados.append({
                    "Local": nome_final,
                    "Tendência": resultado.trend,
                    "p-value": round(resultado.p, 4),
                    "Tau": round(resultado.Tau, 4),
                    "Inclinação (Slope)": round(resultado.slope, 4),
                    "Significativo": "Sim" if resultado.p < 0.05 else "Não"
                })
            
            df_mk_result = pd.DataFrame(lista_resultados)
            print(f"      OK: {len(df_mk_result)} registros processados.")
        except Exception as e:
            print(f"   Erro no teste Mann-Kendall: {e}")
    else:
        print("   [PULADO] Mann-Kendall não executado (biblioteca ausente).")
        
    return df_mk_result
