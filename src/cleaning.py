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
    
    # GARANTIA: Calcular ano_disp a partir da data normalizada para evitar inconsistências do arquivo original
    df_disp['ano_disp'] = df_disp['dt_disp'].dt.year
    
    # Filtro: datas em ou antes da 'data_fechamento' e ano >= 2018
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
    
    # Criar mes_disp (Jan, Fev...) para a tabela de output
    month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    df_disp_semdupl['mes_disp'] = df_disp_semdupl['dt_disp'].dt.month.map(month_map)
    
    return df_disp, df_disp_semdupl