import pandas as pd
import os

file_path = 'df_prep_consolidado.csv'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
else:
    try:
        # Read only the first few rows to inspect columns
        df = pd.read_csv(file_path, sep=';', nrows=5, encoding='latin-1') # Try latin-1 first as it's common in these datasets
        print("Columns:")
        for col in df.columns:
            print(col)
        print("\nHead:")
        print(df.head())
    except Exception as e:
        print(f"Error reading with latin-1: {e}")
        try:
             df = pd.read_csv(file_path, sep=';', nrows=5, encoding='utf-8')
             print("Columns (UTF-8):")
             for col in df.columns:
                 print(col)
        except Exception as e2:
            print(f"Error reading with utf-8: {e2}")
