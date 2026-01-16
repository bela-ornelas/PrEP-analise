import pandas as pd
import sys
import os
import argparse

def check_frequency(column_name, filter_expr=None, file_path='df_prep_consolidado.csv'):
    """
    Lê a base local e imprime a frequência da coluna solicitada, com opção de filtro.
    
    Exemplos de uso:
    1. Simples:
       python check_data.py ano_disp
       
    2. Com filtro (apenas vivos):
       python check_data.py ano_disp --filter "data_obito.isna()"
       
    3. Com filtro (apenas quem faleceu):
       python check_data.py ano_disp --filter "data_obito.notna()"
       
    4. Com filtro de valor (ex: ano > 2020):
       python check_data.py mes_disp --filter "ano_disp > 2020"
    """
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        return

    print(f"Lendo base local: {file_path}...")
    
    try:
        # Se tiver filtro, precisamos carregar as colunas usadas no filtro também
        # Como é difícil saber quais são sem analisar a string, carregamos tudo (ainda é rápido para 300k linhas)
        # Se performance for crítica, podemos otimizar depois.
        df = pd.read_csv(file_path, sep=';', low_memory=False)
        
        # Aplicar Filtro se houver
        if filter_expr:
            print(f"Aplicando filtro: {filter_expr}")
            original_len = len(df)
            try:
                # pandas query engine usa sintaxe python-like ou sql-like
                # Para isna() funcionar no query, usamos engine='python'
                df = df.query(filter_expr, engine='python')
                print(f"Linhas filtradas: {len(df)} (de {original_len})")
            except Exception as e:
                print(f"Erro no filtro: {e}")
                print("Dica: Use sintaxe Pandas, ex: 'coluna == \"Valor\"' ou 'coluna.isna()'")
                return

        if column_name not in df.columns:
            print(f"Erro: A coluna '{column_name}' não existe.")
            return

        print(f"\n--- Frequência da variável: {column_name} ---")
        counts = df[column_name].value_counts(dropna=False).sort_index()
        print(counts)
        
        # Total
        print(f"\nTotal: {len(df)}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consulta rápida de dados do PrEP consolidado.")
    parser.add_argument("coluna", help="Nome da coluna para ver a frequência")
    parser.add_argument("--filter", help="Expressão de filtro (sintaxe Pandas/Python). Ex: 'data_obito.isna()'", default=None)
    
    args = parser.parse_args()
    
    check_frequency(args.coluna, args.filter)