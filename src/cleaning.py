import pandas as pd
from .utils import mes_nome

def clean_disp_df(df_disp, data_fechamento):
    """
    Limpa e prepara o dataframe de dispensas.
    - Converte datas
    - Filtra por data de fechamento e ano >= 2018
    - Remove duplicatas de dia
    - Cria colunas de tempo
    """
    if df_disp.empty:
        return pd.DataFrame(), pd.DataFrame() # Retorna vazio se input vazio

    print("Iniciando limpeza da base de Dispensas...")
    
    # Trabalhando as datas
    df_disp['data_dispensa'] = pd.to_datetime(df_disp['data_dispensa'], dayfirst=True, errors='coerce')
    df_disp['dt_disp'] = df_disp['data_dispensa'].dt.normalize()
    
    df_disp['ano_disp'] = df_disp['dt_disp'].dt.year
    df_disp['mesN_disp'] = df_disp['dt_disp'].dt.month
    
    # Filtro de data
    hoje_dt = pd.to_datetime(data_fechamento).normalize()
    df_disp = df_disp[(df_disp['dt_disp'] <= hoje_dt) & (df_disp['ano_disp'] >= 2018)].copy()
    
    # Coluna mes_disp usando a função utilitaria ou map
    # O notebook usa map de um dict hardcoded. Vamos usar a nossa função utils.mes_nome ou map similar.
    # No notebook: Disp['mes_disp'] = Disp['dt_disp'].dt.month_name().str[:3].map(month_mapping)
    # Nossa função utils.mes_nome faz isso.
    df_disp['mes_disp'] = df_disp['dt_disp'].apply(mes_nome)
    
    # Soma duração
    if 'duracao' in df_disp.columns:
         df_disp['duracao_sum'] = df_disp.groupby(['codigo_pac_eleito', 'dt_disp'])['duracao'].transform('sum')

    # Ordenação
    df_disp = df_disp.sort_values(['codigo_pac_eleito', 'dt_disp'], ascending=[True, False])
    
    # Deduplicação (cria Disp_semdupl)
    df_disp_semdupl = df_disp.drop_duplicates(subset=['codigo_pac_eleito', 'dt_disp']).copy()

    # Mapeamento UF UDM
    # Disp['Cod_IBGE'] = Disp['cod_ibge_udm'].astype(str)
    # Disp['Cod_UF'] = Disp['Cod_IBGE'].str[:2]
    # No notebook isso é feito antes de dup, mas tanto faz. Faremos no dataframe limpo.
    
    # Vamos aplicar no semdupl também ou passar para preprocessing
    return df_disp, df_disp_semdupl
