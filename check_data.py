import pandas as pd
import sys
import os

def check_frequency(column_name, file_path='df_prep_consolidado.csv'):
    """
    Lê o arquivo consolidado local e imprime a frequência da coluna solicitada.
    """
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        print("Certifique-se de rodar o 'main.py' pelo menos uma vez para gerar a base.")
        return

    print(f"Lendo base local: {file_path}...")
    try:
        # Carregando a base (usando apenas a coluna necessária para ser ainda mais rápido)
        df = pd.read_csv(file_path, sep=';', usecols=[column_name], low_memory=False)
        
        print(f"\n--- Frequência da variável: {column_name} ---")
        counts = df[column_name].value_counts(dropna=False).sort_index()
        print(counts)
        
        # Se for numérica, mostra um resumo simples
        if pd.api.types.is_numeric_dtype(df[column_name]):
            print("\n--- Resumo Estatístico ---")
            print(df[column_name].describe())
            
    except ValueError:
        print(f"Erro: A coluna '{column_name}' não existe no arquivo.")
        # Opcional: mostrar colunas disponíveis
        temp_df = pd.read_csv(file_path, sep=';', nrows=0)
        print(f"Colunas disponíveis: {list(temp_df.columns)}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        col = sys.argv[1]
        check_frequency(col)
    else:
        print("Uso: python check_data.py NOME_DA_COLUNA")
        print("Exemplo: python check_data.py ano_disp")
