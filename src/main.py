import argparse
import os
import pandas as pd
import datetime
from .config import MONTHS_ORDER
from .data_loader import carregar_bases
from .cleaning import clean_disp_df
from .preprocessing import enrich_disp_data, calculate_intervals, flag_first_last_disp
from .analysis import generate_disp_metrics, generate_new_users_metrics, generate_prep_history

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
    # Apenas Dispensa e Cadastro são essenciais para as métricas pedidas
    bases = carregar_bases(data_fechamento, carregar_disp=True, carregar_cad=True, carregar_pvha=True)
    
    df_disp = bases.get("Disp", pd.DataFrame())
    df_cad = bases.get("Cadastro_HIV", pd.DataFrame())
    df_pvha = bases.get("PVHA", pd.DataFrame())
    df_pvha_prim = bases.get("PVHA_Prim", pd.DataFrame())
    
    if df_disp.empty:
        print("Erro: Base de dispensas vazia ou não encontrada.")
        return

    # 2. Limpeza
    df_disp, df_disp_semdupl = clean_disp_df(df_disp, args.data_fechamento)
    
    # 3. Processamento
    df_disp_semdupl = enrich_disp_data(df_disp_semdupl, df_cad, df_pvha, df_pvha_prim)
    df_disp_semdupl = calculate_intervals(df_disp_semdupl)
    df_disp_semdupl = flag_first_last_disp(df_disp_semdupl)
    
    # 4. Análise e Outputs
    # a) Dispensas por Mês/Ano
    disp_metrics = generate_disp_metrics(df_disp_semdupl)
    print("\n--- Dispensas por Mês/Ano ---")
    print(disp_metrics)
    
    # b) Novos Usuários por Mês/Ano
    new_users_metrics = generate_new_users_metrics(df_disp_semdupl)
    print("\n--- Novos Usuários por Mês/Ano ---")
    print(new_users_metrics)
    
    # c) Classificações (12m, EmPrEP)
    # c) Classificações (12m, EmPrEP)
    from .analysis import classify_prep_users
    classificacoes = classify_prep_users(df_disp_semdupl, args.data_fechamento)
    
    label_12m_sim = "Teve dispensação nos últimos 12 meses"
    label_12m_nao = "Não teve dispensação nos últimos 12 meses"
    
    val_12m_sim = classificacoes.get('Disp_Ultimos_12m', 0)
    val_12m_nao = classificacoes.get('Disp_Ultimos_12m_Nao', 0)
    val_emprep = classificacoes.get('EmPrEP_Atual', 0)
    val_descont = classificacoes.get('Descontinuados', 0)
    
    print("\n--- Frequências Atuais ---")
    print(f"{label_12m_sim}: {val_12m_sim}")
    print(f"{label_12m_nao}: {val_12m_nao}")
    print(f"Em PrEP atualmente: {val_emprep}")
    print(f"Estão descontinuados: {val_descont}")
    
    # d) Histórico EmPrEP
    df_history = generate_prep_history(df_disp_semdupl, args.data_fechamento)
    print("\n--- Histórico de Adesão (2018 - Presente) ---")
    print(df_history.to_string(index=False))
    
    # Exportação
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    disp_file = os.path.join(args.output_dir, "Dispensas_Mes_Ano.csv")
    new_users_file = os.path.join(args.output_dir, "Novos_Usuarios_Mes_Ano.csv")
    class_file = os.path.join(args.output_dir, "Classificacoes.txt")
    history_file = os.path.join(args.output_dir, "EmPrEP_Historico.csv")
    
    disp_metrics.to_csv(disp_file, sep=";")
    new_users_metrics.to_csv(new_users_file, sep=";")
    df_history.to_csv(history_file, sep=";", index=False)
    
    with open(class_file, "w", encoding='utf-8') as f:
        f.write(f"{label_12m_sim}: {val_12m_sim}\n")
        f.write(f"{label_12m_nao}: {val_12m_nao}\n")
        f.write(f"Em PrEP atualmente: {val_emprep}\n")
        f.write(f"Estão descontinuados: {val_descont}\n")
    
    print(f"\nOutputs salvos em: {args.output_dir}")

if __name__ == "__main__":
    main()
