import pandas as pd
import numpy as np
import os
import sys

try:
    import win32com.client
    HAS_COM = True
except ImportError:
    HAS_COM = False

# Define file paths
PREP_FILE = 'df_prep_consolidado.csv'
TARV_FILE = r'//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PVHA_prim_ult.csv'

def load_and_merge():
    print(">>> Carregando dados...")
    
    # 1. Load PrEP with Demographics
    cols_prep = [
        'Cod_unificado', 'codigo_pac_eleito', 'dt_disp_max', 'dt_disp_min',
        'Pop_genero_pratica', 'fetar', 'raca4_cat', 'escol4', 'uf_residencia'
    ]
    # Check if files exist
    if not os.path.exists(PREP_FILE):
        print(f"Erro: Arquivo PrEP não encontrado: {PREP_FILE}")
        sys.exit(1)
        
    df_prep = pd.read_csv(PREP_FILE, sep=';', encoding='latin-1', usecols=lambda c: c in cols_prep)
    
    # 2. Load TARV
    cols_tarv = ['Cod_unificado', 'data_dispensa_prim']
    df_tarv = pd.read_csv(TARV_FILE, sep=';', encoding='latin-1', usecols=cols_tarv, low_memory=True)
    
    # 3. Process Dates
    df_prep['dt_disp_max'] = pd.to_datetime(df_prep['dt_disp_max'], errors='coerce')
    df_tarv['data_dispensa_prim'] = pd.to_datetime(df_tarv['data_dispensa_prim'], dayfirst=True, errors='coerce')
    
    # 4. Merge
    df_merged = pd.merge(df_prep, df_tarv, on='Cod_unificado', how='inner', suffixes=('_prep', '_tarv'))
    
    # 5. Calculate Diff
    df_merged['days_diff'] = (df_merged['data_dispensa_prim'] - df_merged['dt_disp_max']).dt.days
    
    return df_merged

def generate_demographic_summary(df):
    """Generates a text summary of demographics."""
    summary_lines = []
    
    cols_map = {
        'Pop_genero_pratica': 'População Chave',
        'fetar': 'Faixa Etária',
        'raca4_cat': 'Raça/Cor',
        'escol4': 'Escolaridade',
        'uf_residencia': 'UF de Residência'
    }
    
    total = len(df)
    
    for col, nice_name in cols_map.items():
        if col in df.columns:
            summary_lines.append(f"\n--- {nice_name} ---")
            counts = df[col].value_counts(dropna=False)
            freqs = df[col].value_counts(normalize=True, dropna=False) * 100
            
            for cat, count in counts.items():
                cat_label = str(cat) if pd.notna(cat) else "Não Informado/Ignorado"
                perc = freqs[cat]
                summary_lines.append(f"{cat_label}: {count} ({perc:.1f}%)")
    
    return "\n".join(summary_lines)

def create_word_doc(stats_text, demog_text):
    if not HAS_COM:
        print("Win32COM não disponível. Pulando criação do Word.")
        return

    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Add()
        
        # Styles
        def add_para(text, bold=False, size=11):
            p = doc.Content.Paragraphs.Add()
            p.Range.Text = text
            p.Range.Font.Size = size
            p.Range.Font.Bold = bold
            p.Range.InsertParagraphAfter()
            return p

        add_para("Relatório Detalhado: PrEP e Transição para TARV", bold=True, size=16)
        add_para("Data: 23 de janeiro de 2026\n", size=10)
        
        # Section 1: Summary
        add_para("1. Resumo da Análise Temporal", bold=True, size=12)
        add_para(stats_text)
        
        # Section 2: Demographics
        add_para("\n2. Perfil Sociodemográfico (Usuários que iniciaram TARV APÓS a PrEP)", bold=True, size=12)
        add_para("Este perfil considera apenas os usuários cuja primeira dispensa de TARV ocorreu após a data da última dispensa de PrEP (Conversão Pós-PrEP).\n")
        add_para(demog_text, size=10)
        
        # Section 3: Inconsistencies
        add_para("\n3. Inconsistências Identificadas", bold=True, size=12)
        add_para("Foi gerado um arquivo Excel ('Inconsistencias_PrEP_TARV.xlsx') contendo a lista de códigos dos casos onde a data de início de TARV é anterior ou igual à data da última dispensa de PrEP.")

        # Save
        filename = os.path.abspath("Relatorio_Analise_PrEP_TARV_v2.docx")
        doc.SaveAs(filename)
        doc.Close()
        word.Quit()
        print(f"Documento Word salvo em: {filename}")
        
    except Exception as e:
        print(f"Erro ao gerar Word: {e}")

def main():
    df = load_and_merge()
    
    # Split
    df_valid = df[df['days_diff'] > 0].copy()
    df_error = df[df['days_diff'] <= 0].copy()
    
    print(f"Total Intersecção: {len(df)}")
    print(f"Transições Válidas (Pós-PrEP): {len(df_valid)}")
    print(f"Inconsistências (TARV <= PrEP): {len(df_error)}")
    
    # 1. Generate Excel for Errors
    if not df_error.empty:
        print("Gerando Excel de inconsistências...")
        cols_export = ['Cod_unificado', 'codigo_pac_eleito', 'dt_disp_min', 'dt_disp_max', 'data_dispensa_prim', 'days_diff', 'uf_residencia']
        # Filter columns that actually exist
        cols_export = [c for c in cols_export if c in df_error.columns]
        df_error[cols_export].to_excel("Inconsistencias_PrEP_TARV.xlsx", index=False)
        print("Arquivo 'Inconsistencias_PrEP_TARV.xlsx' salvo com sucesso.")
    
    # 2. Generate Demographic Stats for Valid Group
    print("Calculando demografia do grupo válido...")
    demog_text = generate_demographic_summary(df_valid)
    
    # 3. Prepare Stats Text
    stats_text = (
        f"Total de usuários na intersecção: {len(df)}.\n\n"
        f"Grupo A: Transição Pós-PrEP (Válidos): {len(df_valid)} ({len(df_valid)/len(df)*100:.1f}%)\n"
        f"Grupo B: Inconsistências (TARV iniciada antes ou durante a PrEP): {len(df_error)} ({len(df_error)/len(df)*100:.1f}%)\n\n"
        "Análise de Tempo (Grupo A):\n"
        f"Média de dias entre fim da PrEP e início da TARV: {df_valid['days_diff'].mean():.1f} dias.\n"
        f"Mediana: {df_valid['days_diff'].median():.1f} dias."
    )
    
    # 4. Generate Word Doc
    create_word_doc(stats_text, demog_text)

if __name__ == "__main__":
    main()
