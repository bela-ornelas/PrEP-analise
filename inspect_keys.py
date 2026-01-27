import pickle
import pandas as pd

cache_path = r".cache/bases_2025-12-31.pkl"
with open(cache_path, 'rb') as f:
    data = pickle.load(f)

print("--- PVHA_Prim Columns ---")
print(data['PVHA_Prim'].columns.tolist())
print(data['PVHA_Prim'].head(2))

print("\n--- Cadastro_HIV Columns ---")
print(data['Cadastro_HIV'][['codigo_paciente', 'Cod_unificado']].head(2))

print("\n--- Cadastro_PrEP Columns ---")
print(data['Cadastro_PrEP'].columns.tolist())
