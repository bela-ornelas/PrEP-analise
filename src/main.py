import argparse
import os
import time
import pandas as pd
from .config import MONTHS_ORDER
from .data_loader import carregar_bases
from .cleaning import clean_disp_df, process_cadastro
from .preprocessing import enrich_disp_data, calculate_intervals, flag_first_last_disp
from .analysis import generate_disp_metrics, generate_new_users_metrics, generate_prep_history, generate_prep_history_legacy, classify_prep_users, generate_population_metrics, classify_udm_active, generate_annual_summary
from .prep_consolidation import create_prep_dataframe
from .excel_generator import export_to_excel
from .visualization import plot_dispensations, plot_cascade
from .optimization_tools import measure_time, compare_dataframes

def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Monitoramento PrEP CLI")
    parser.add_argument("--data_fechamento", required=True, help="Data de fechamento no formato YYYY-MM-DD (Ex: 2025-09-30)")
    parser.add_argument("--output_dir", default=".", help="Diretório para salvar os outputs")
    parser.add_argument("--no_cache", action="store_true", help="Força o recarregamento das bases da rede, ignorando o cache local.")
    
    args = parser.parse_args()
    
    # Validar Data
    try:
        data_fechamento = pd.to_datetime(args.data_fechamento).date()
    except ValueError:
        print("Erro: Formato de data inválido. Use YYYY-MM-DD.")
        return

    print(f"Executando Monitoramento PrEP para data: {data_fechamento}")
    
    # 1. Carregar Bases
    # carregar_disp=True, carregar_cad=True, carregar_pvha=True -> Carrega tudo que precisamos
    bases = carregar_bases(data_fechamento, carregar_disp=True, carregar_cad=True, carregar_pvha=True, use_cache=not args.no_cache)
    
    df_disp = bases.get("Disp", pd.DataFrame())
    df_cad_prep = bases.get("Cadastro_PrEP", pd.DataFrame()) # Demográfico
    df_cad_hiv = bases.get("Cadastro_HIV", pd.DataFrame())   # PVHA (Cod_unificado)
    df_pvha = bases.get("PVHA", pd.DataFrame())
    df_pvha_prim = bases.get("PVHA_Prim", pd.DataFrame())
    df_ibge = bases.get("Tabela_IBGE", pd.DataFrame())
    
    if df_disp.empty:
        print("Erro: Base de dispensas vazia ou não encontrada.")
        return

    # Processar Cadastro (Normalizar datas e deduplicar)
    df_cad_prep = process_cadastro(df_cad_prep)

    # 2. Limpeza (Conforme orientações estritas)
    df_disp, df_disp_semdupl = clean_disp_df(df_disp, args.data_fechamento)
    
    # 3. Processamento (Enriquecimento completo com os 4 merges)
    df_disp_semdupl = enrich_disp_data(df_disp_semdupl, df_cad_prep, df_cad_hiv, df_pvha, df_pvha_prim, df_ibge)
    df_disp_semdupl = calculate_intervals(df_disp_semdupl)
    df_disp_semdupl = flag_first_last_disp(df_disp_semdupl)
    
    # 4. Análise e Outputs
    # a) Histórico EmPrEP Detalhado (Gera flags no dataframe e tabela histórica)
    df_disp_semdupl, df_history = generate_prep_history(df_disp_semdupl, args.data_fechamento)
    
    # b) Classificação UDM Ativa
    df_disp_semdupl = classify_udm_active(df_disp_semdupl, args.data_fechamento)

    # 5. Consolidação Final (df PrEP - Uma linha por paciente)
    df_prep = create_prep_dataframe(df_disp_semdupl, df_cad_prep, df_cad_hiv, df_pvha, df_pvha_prim)
    
    print(f"\n--- DataFrame Consolidado 'df PrEP' ---")
    print(f"Linhas: {len(df_prep)} (Deve bater com usuários únicos no cadastro)")
    print(f"Colunas: {len(df_prep.columns)}")
    
    # 6. Salvar df_prep em CSV (Opcional, mas útil para conferência)
    prep_file = os.path.join(args.output_dir, "df_prep_consolidado.csv")
    print(f"Salvando base consolidada em: {prep_file}")
    df_prep.to_csv(prep_file, sep=';', index=False)
    
    # Gerar Gráfico de Cascata
    plot_cascade(df_prep, args.output_dir)

    # c) Classificações Atuais (12m, EmPrEP) 
    classificacoes = classify_prep_users(df_prep, args.data_fechamento)
    
    # -------------------------------------------------------------------------
    # CONFERÊNCIA DE VALORES
    # -------------------------------------------------------------------------
    print("\n--- Conferência EmPrEP_Atual ---")
    if "EmPrEP_Atual" in df_prep.columns:
        print(df_prep["EmPrEP_Atual"].value_counts())
    
    # d) Dispensas por Mês/Ano
    disp_metrics = generate_disp_metrics(df_disp_semdupl)
    print("\n--- Dispensas por Mês/Ano ---")
    print(disp_metrics)
    
    # Gerar Gráfico
    plot_dispensations(df_disp_semdupl, args.data_fechamento, args.output_dir)
    
    # e) Novos Usuários por Mês/Ano
    new_users_metrics = generate_new_users_metrics(df_prep)
    
    # f) Populações (apenas Em PrEP atualmente)
    pop_metrics = generate_population_metrics(df_prep)
    
    # g) Resumo Anual (Nova Aba)
    annual_summary = generate_annual_summary(df_prep, args.data_fechamento)
    
    # Exportação
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    metrics_to_export = {
        'classificacoes': classificacoes,
        'disp_mes_ano': disp_metrics,
        'novos_usuarios': new_users_metrics,
        'historico': df_history, 
        'populacoes': pop_metrics,
        'annual_summary': annual_summary
    }
    
    excel_file = export_to_excel(args.output_dir, args.data_fechamento, metrics_to_export)
    
    # Manter CSVs antigos para retrocompatibilidade
    disp_metrics.to_csv(os.path.join(args.output_dir, "Dispensas_Mes_Ano.csv"), sep=";")
    new_users_metrics.to_csv(os.path.join(args.output_dir, "Novos_Usuarios_Mes_Ano.csv"), sep=";")

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    print(f"\nTempo total de execução: {minutes}m {seconds}s")

if __name__ == "__main__":
    main()