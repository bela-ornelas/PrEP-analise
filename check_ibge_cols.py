import pandas as pd
import os

path = "M:/Arquivos Atuais/Tabelas IBGE/Tabela_IBGE_UF e Municípios.xlsx"

if os.path.exists(path):
    try:
        df = pd.read_excel(path, nrows=5)
        print("Colunas encontradas:")
        print(df.columns.tolist())
    except Exception as e:
        print(f"Erro ao ler Excel: {e}")
else:
    print("Arquivo não encontrado no caminho padrão.")
