import argparse
import os
import pandas as pd
import datetime
from .config import MONTHS_ORDER
from .data_loader import carregar_bases
from .cleaning import clean_disp_df, process_cadastro
from .preprocessing import enrich_disp_data, calculate_intervals, flag_first_last_disp
from .analysis import generate_disp_metrics, generate_new_users_metrics, generate_prep_history, classify_prep_users, generate_population_metrics, classify_udm_active
from .excel_generator import export_to_excel

def main():
    parser = argparse.ArgumentParser(description="Monitoramento PrEP CLI")
    parser.add_argument("--data_fechamento", required=True, help="Data de fechamento no formato YYYY-MM-DD (Ex: 2025-09-30)")
    parser.add_argument("--output_dir", default=".", help="Diretório para salvar os outputs")
    
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
    bases = carregar_bases(data_fechamento, carregar_disp=True, carregar_cad=True, carregar_pvha=True)
    
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

    # c) Classificações Atuais (12m, EmPrEP) 
    classificacoes = classify_prep_users(df_disp_semdupl, args.data_fechamento)
    
    # -------------------------------------------------------------------------
    # CONFERÊNCIA DE VALORES (Prints solicitados)
    # -------------------------------------------------------------------------
    print("\n--- Conferência EmPrEP_Atual ---")
    if "EmPrEP_Atual" in df_disp_semdupl.columns:
        print(df_disp_semdupl.drop_duplicates("codigo_pac_eleito")["EmPrEP_Atual"].value_counts())
    print()

    data_dt = pd.to_datetime(args.data_fechamento)
    for ano_e in range(data_dt.year, 2017, -1):
        col_name = f"EmPrEP_{ano_e}"
        if col_name in df_disp_semdupl.columns:
            print(f"--- Contagem {col_name} ---")
            print(pd.DataFrame(df_disp_semdupl.drop_duplicates("codigo_pac_eleito")[col_name].value_counts()))
            print()
    
    # d) Dispensas por Mês/Ano
    disp_metrics = generate_disp_metrics(df_disp_semdupl)
    print("\n--- Dispensas por Mês/Ano ---")
    print(disp_metrics)
    
    # e) Novos Usuários por Mês/Ano
    new_users_metrics = generate_new_users_metrics(df_disp_semdupl)
    
    # f) Populações (apenas Em PrEP atualmente)
    pop_metrics = generate_population_metrics(df_disp_semdupl)
    
    print("\n--- Resultados Processados ---")
    print(f"Em PrEP atualmente: {classificacoes['EmPrEP_Atual']}")
    print("\n--- Histórico Mensal (Últimos 5 registros) ---")
    if not df_history.empty:
        print(df_history.tail().to_string(index=False))
    
    print("\n" + "="*50)
    print("CONFERÊNCIA DE CADASTRO")
    if 'codigo_pac_eleito' in df_cad_prep.columns:
        print(f"Número de usuários únicos no Cadastro (pac_eleito): {df_cad_prep['codigo_pac_eleito'].nunique()}")
    elif 'codigo_paciente' in df_cad_prep.columns:
        print(f"Número de usuários únicos no Cadastro (paciente): {df_cad_prep['codigo_paciente'].nunique()}")
    else:
        print("Coluna de identificação de paciente não encontrada no Cadastro para conferência.")
    print("="*50 + "\n")

    # Exportação
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    metrics_to_export = {
        'classificacoes': classificacoes,
        'disp_mes_ano': disp_metrics,
        'novos_usuarios': new_users_metrics,
        'historico': df_history, # Tabela mensal detalhada
        'populacoes': pop_metrics
    }
    
    excel_file = export_to_excel(args.output_dir, args.data_fechamento, metrics_to_export)
    
    # Manter CSVs antigos para retrocompatibilidade se desejar
    disp_metrics.to_csv(os.path.join(args.output_dir, "Dispensas_Mes_Ano.csv"), sep=";")
    new_users_metrics.to_csv(os.path.join(args.output_dir, "Novos_Usuarios_Mes_Ano.csv"), sep=";")
    
    print(f"\nOutputs salvos em: {args.output_dir}")
    print(f"Conferência Final: Número de usuários únicos no Cadastro: {df_cad_prep['codigo_pac_eleito'].nunique()}")

if __name__ == "__main__":
    main()