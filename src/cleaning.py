import pandas as pd
import numpy as np

def clean_disp_df(df_disp, data_fechamento):
    """
    Limpa e prepara o dataframe de dispensas conforme lógica estrita fornecida.
    """
    if df_disp.empty:
        return pd.DataFrame(), pd.DataFrame()

    print("Iniciando limpeza da base de Dispensas...")
    
    # 1) Converta a coluna "data_dispensa" para datetime com errors="coerce".
    df_disp["data_dispensa"] = pd.to_datetime(df_disp["data_dispensa"], errors="coerce")
    
    # 2) Crie a coluna "dt_disp" como a versão normalizada (sem hora) de "data_dispensa".
    df_disp["dt_disp"] = df_disp["data_dispensa"].dt.normalize()
    
    # Garantir ano_disp para o filtro (usando a coluna do banco ou extraindo da data)
    if 'ano_disp' not in df_disp.columns:
        df_disp['ano_disp'] = df_disp['dt_disp'].dt.year
    
    # Filtro
    hoje2_dt = pd.to_datetime(data_fechamento).normalize()
    df_disp = df_disp[(df_disp['dt_disp'] <= hoje2_dt) & (df_disp['ano_disp'] >= 2018)]

    # Soma a duração de cod_pac e dt_disp iguais.
    if 'duracao' in df_disp.columns:
        df_disp['duracao'] = pd.to_numeric(df_disp['duracao'], errors='coerce').fillna(0)
        df_disp['duracao_sum'] = df_disp.groupby(['codigo_pac_eleito', 'dt_disp'])['duracao'].transform('sum')

    # ordenar por cod_pac e dt_disp
    df_disp = df_disp.sort_values(['codigo_pac_eleito', 'dt_disp'], ascending = [True, False])

    # retira duplicidade de data da dispensa e cria novo banco "Disp_semdupl".
    df_disp_semdupl = df_disp.drop_duplicates(subset=['codigo_pac_eleito', 'dt_disp']).copy()
    
    # Adicionar mes_disp para o relatório final
    month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    df_disp_semdupl['mes_disp'] = df_disp_semdupl['dt_disp'].dt.month.map(month_map)
    
    return df_disp, df_disp_semdupl

def process_cadastro(df_cad):
    """
    Limpa e normaliza o dataframe de Cadastro PrEP.
    - Normaliza datas (nascimento, cadastro, atualização)
    - Remove duplicatas por codigo_pac_eleito
    """
    if df_cad.empty:
        return df_cad

    print("Iniciando processamento do Cadastro...")
    
    # Padronizar nome da data de nascimento se necessário
    if 'data_nascimento' not in df_cad.columns and 'dt_nasc' in df_cad.columns:
        print("Renomeando/Copiando 'dt_nasc' para 'data_nascimento'")
        df_cad['data_nascimento'] = df_cad['dt_nasc']

    # Lista de colunas de data para normalizar
    # Verifica nomes comuns e variações
    date_cols = ['data_nascimento', 'dt_nasc', 'data_cadastro', 'dt_cadas', 'data_ult_atu', 'dt_ult_atu']
    
    for col in date_cols:
        if col in df_cad.columns:
            df_cad[col] = pd.to_datetime(df_cad[col], errors='coerce').dt.normalize()
    
    # Remover duplicatas mantendo a primeira ocorrência
    if 'codigo_pac_eleito' in df_cad.columns:
        df_cad.drop_duplicates("codigo_pac_eleito", keep="last", inplace=True)
        print(f"Cadastro deduplicado (codigo_pac_eleito). Total: {len(df_cad)}")
    elif 'codigo_paciente' in df_cad.columns:
        df_cad.drop_duplicates("codigo_paciente", keep="last", inplace=True)
        print(f"Cadastro deduplicado (codigo_paciente). Total: {len(df_cad)}")
        
    return df_cad
