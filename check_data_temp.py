import pandas as pd
import pickle

path = '.cache/bases_2025-12-31.pkl'
try:
    data = pd.read_pickle(path)
    print(f"Arquivo carregado com sucesso: {path}")
    
    if isinstance(data, dict):
        print(f"Chaves no dicionário: {list(data.keys())}")
        if 'PrEP' in data:
            df = data['PrEP']
        else:
            print("Chave 'PrEP' não encontrada. Usando o primeiro DataFrame disponível.")
            df = data[list(data.keys())[0]]
    else:
        df = data

    print("\n--- Informações do DataFrame PrEP ---")
    print(f"Número de linhas: {df.shape[0]}")
    print(f"Número de colunas: {df.shape[1]}")
    print("\n--- Colunas ---")
    print(df.columns.tolist())
    print("\n--- Primeiras 3 linhas ---")
    print(df.head(3))
    print("\n--- Estatísticas básicas (numéricas) ---")
    print(df.describe())

except Exception as e:
    print(f"Erro ao ler o arquivo: {e}")
