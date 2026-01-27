import pandas as pd
import sys
import os
import glob

# Adiciona o diretório atual ao path
sys.path.append(os.getcwd())

from src.indicador_prep_hiv import calcular_denominador_hiv

def load_pvha_check():
    # Tenta achar o arquivo parquet local ou na rede (caminho padrao do script)
    candidates = [
        "PVHA_prim_ult.parquet",
        "//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PVHA_prim_ult.parquet"
    ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"Base PVHA encontrada em: {path}")
            try:
                return pd.read_parquet(path)
            except Exception as e:
                print(f"Erro ao ler {path}: {e}")
    
    print("ERRO: Não foi possível encontrar 'PVHA_prim_ult.parquet' no diretório local ou na rede.")
    return pd.DataFrame()

def main():
    print("--- VERIFICAÇÃO DE NÚMEROS: VINCULADOS HIV (DENOMINADOR) ---")
    
    df_pvha = load_pvha_check()
    
    if df_pvha.empty:
        print("Abortando verificação por falta de dados.")
        return

    # Normalizar datas se necessario (como feito no script original)
    if "Menor Data" not in df_pvha.columns and "data_min" in df_pvha.columns:
        df_pvha["Menor Data"] = pd.to_datetime(df_pvha["data_min"], errors="coerce")

    # Definir data de fechamento conforme seu pedido (Julho 2025 para cobrir a tabela)
    # A tabela vai até 7_2025.
    DATA_FECHAMENTO = '2025-07-31'
    
    # Calcular
    print(f"Calculando dados até {DATA_FECHAMENTO}...")
    df_resultados = calcular_denominador_hiv(df_pvha, DATA_FECHAMENTO)
    
    if df_resultados.empty:
        print("Cálculo retornou vazio.")
        return
        
    # Filtrar para exibir igual sua tabela (Transposta: Linhas=Locais, Colunas=Datas)
    # O script original retorna Linhas=Datas, Colunas=Municipios. Vamos transpor de volta.
    df_check = df_resultados.T
    
    # Mapear códigos IBGE para nomes para facilitar a leitura (Ex: Manaus, Brasil)
    # Brasil é a soma de tudo? O script original calcula município a município.
    # Sua tabela tem "Brasil" e "Manaus".
    
    # 1. Calcular BRASIL (Soma de todas as colunas do resultado original [que são municipios])
    # O df_resultados original tem index=Data, columns=CodIBGE
    
    serie_brasil = df_resultados.sum(axis=1) # Soma de todos os municipios por data
    
    # 2. Calcular MANAUS (IBGE 1302603)
    # Codigo IBGE de Manaus é 130260 ou 1302603
    cod_manaus = '1302603'
    if cod_manaus not in df_resultados.columns:
        cod_manaus = '130260' # Tentativa 6 digitos
    
    serie_manaus = pd.Series(0, index=df_resultados.index)
    if cod_manaus in df_resultados.columns:
        serie_manaus = df_resultados[cod_manaus]
    else:
        print(f"Aviso: Código IBGE de Manaus ({cod_manaus}) não encontrado nas colunas.")

    # 3. Montar tabela comparativa para datas chaves
    datas_chave = [
        '2022-01-31', # 1_2022
        '2022-12-31', # 12_2022
        '2023-01-31', # 1_2023
        '2024-01-31', # 1_2024
        '2025-07-31'  # 7_2025
    ]
    
    print("\n" + "="*60)
    print(f"{ 'DATA (Mês_Ano)':<15} | { 'MANAUS (Calc)':<15} | { 'MANAUS (Ref)':<15} | { 'BRASIL (Calc)':<15} | { 'BRASIL (Ref)':<15}")
    print("="*60)
    
    # Valores de referência da sua tabela
    ref_vals = {
        '2022-01-31': {'Manaus': 1044.0, 'Brasil': 33055.0},
        '2022-12-31': {'Manaus': 953.0,  'Brasil': 32937.0},
        '2023-01-31': {'Manaus': 963.0,  'Brasil': 33697.0},
        '2024-01-31': {'Manaus': 1008.0, 'Brasil': 34555.0},
        '2025-07-31': {'Manaus': 982.0,  'Brasil': 33101.0}
    }
    
    for dt_str in datas_chave:
        dt = pd.to_datetime(dt_str)
        # Tentar achar a data no index (o index pode ser fim de mes ou inicio, vamos checar)
        # O script original usa pd.date_range(freq='ME'), que gera o último dia do mês.
        
        # Ajuste para encontrar a data mais proxima ou exata
        try:
            val_manaus = serie_manaus.loc[dt]
            val_brasil = serie_brasil.loc[dt]
        except KeyError:
            # Tentar normalizar ou buscar string
            print(f"Data {dt_str} não encontrada no índice.")
            val_manaus = -1
            val_brasil = -1
            
        ref_manaus = ref_vals.get(dt_str, {}).get('Manaus', '-')
        ref_brasil = ref_vals.get(dt_str, {}).get('Brasil', '-')
        
        # Formatação Data para print
        lbl_data = f"{dt.month}_{dt.year}"
        
        print(f"{lbl_data:<15} | {val_manaus:<15.1f} | {ref_manaus:<15} | {val_brasil:<15.1f} | {ref_brasil:<15}")

    print("="*60)

if __name__ == "__main__":
    main()
