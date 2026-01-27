import pandas as pd
import pickle
import sys

# 1. Load PrEP Data
try:
    df_prep = pd.read_csv('df_prep_consolidado.csv', sep=';', encoding='latin1', low_memory=False)
    print("PrEP Columns:", df_prep.columns.tolist())
except Exception as e:
    print(f"Error reading PrEP CSV: {e}")
    sys.exit(1)

# 2. Load Pickle Data
try:
    with open('.cache/bases_2025-12-31.pkl', 'rb') as f:
        data = pickle.load(f)
except Exception as e:
    print(f"Error reading Pickle: {e}")
    sys.exit(1)

df_pvha_prim = data['PVHA_Prim']
df_cadastro_hiv = data['Cadastro_HIV']

# 3. Analyze Linkage
# We need to link df_prep -> PVHA.
# Assumption: df_prep has 'co_paciente' or similar that matches 'codigo_paciente' in Cadastro_HIV.
# Cadastro_HIV maps 'codigo_paciente' -> 'Cod_unificado'.
# PVHA_Prim uses 'Cod_unificado'.

print("\n--- Sample IDs ---")
print(f"PrEP (first 5): {df_prep['co_paciente'].head().tolist() if 'co_paciente' in df_prep.columns else 'co_paciente not found'}")
