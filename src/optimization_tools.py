import time
import pandas as pd
import numpy as np

def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        print(f"--- [START] {func.__name__} ---")
        result = func(*args, **kwargs)
        end = time.time()
        print(f"--- [END] {func.__name__} took {end - start:.4f} sec ---")
        return result
    return wrapper

def compare_dataframes(df_old, df_new, name="Check"):
    print(f"\n[{name}] Comparando DataFrames...")
    if df_old.empty and df_new.empty:
        print("Ambos vazios. OK.")
        return True
        
    # 1. Shape
    if df_old.shape != df_new.shape:
        print(f"ERRO: Shapes diferentes! Old: {df_old.shape}, New: {df_new.shape}")
        return False
        
    # 2. Columns
    # Normalizar ordem para comparação
    cols_old = sorted(list(df_old.columns))
    cols_new = sorted(list(df_new.columns))
    
    if cols_old != cols_new:
        print(f"ERRO: Colunas diferentes!")
        print(f"Old only: {set(df_old.columns) - set(df_new.columns)}")
        print(f"New only: {set(df_new.columns) - set(df_old.columns)}")
        return False
        
    # 3. Sort before comparing values (crucial)
    # Tenta ordenar por codigo_pac_eleito e data se existirem
    sort_cols = []
    if 'codigo_pac_eleito' in df_old.columns: sort_cols.append('codigo_pac_eleito')
    elif 'codigo_paciente' in df_old.columns: sort_cols.append('codigo_paciente')
    
    if 'dt_disp' in df_old.columns: sort_cols.append('dt_disp')
    
    if sort_cols:
        # Check if columns exist
        sort_cols = [c for c in sort_cols if c in df_old.columns]
        
    try:
        if sort_cols:
            df_old_s = df_old.sort_values(sort_cols).reset_index(drop=True)
            df_new_s = df_new.sort_values(sort_cols).reset_index(drop=True)
        else:
            df_old_s = df_old.reset_index(drop=True)
            df_new_s = df_new.reset_index(drop=True)
            
        # Alinhar colunas
        df_new_s = df_new_s[df_old_s.columns]

        pd.testing.assert_frame_equal(df_old_s, df_new_s, check_dtype=False, check_like=True, atol=1e-5)
        print("DataFrames IDÊNTICOS (conteúdo). OK.")
        return True
    except AssertionError as e:
        print(f"ERRO: Conteúdo diverge: {e}")
        return False
