import pandas as pd
import numpy as np
from .config import UF_MAP, REGIAO_MAP

def calculate_population_groups(df):
    """
    Calcula grupos populacionais (HSH, Travesti, MulherTrans, etc.) baseado nas colunas do Cadastro.
    As colunas DEVEM existir no dataframe vindo do merge com o Cadastro.
    """
    # Verificar se as colunas essenciais estão presentes
    required_cols = ['st_orgao_genital', 'tp_sexo_atrib_nasc', 'co_genero', 'co_orientacao_sexual']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"ERRO CRÍTICO: As seguintes colunas demográficas não foram encontradas no DataFrame: {missing_cols}")
        print("Colunas disponíveis:", list(df.columns))

    # Normalizar strings para evitar erros de case/espaço
    for col in required_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # HSH
    cond_hsh = [
        (((df['st_orgao_genital'] == "Pênis") | (df['st_orgao_genital'] == "Vagina e Pênis")) |
         ((df['tp_sexo_atrib_nasc'] == "Masculino") | (df['tp_sexo_atrib_nasc'] == "Intersexo"))) &
        (df['co_genero'] == "Homem CIS") &
        ((df['co_orientacao_sexual'] == "Homossexual / Gay / Lésbica") | (df['co_orientacao_sexual'] == "Bissexual"))
    ]
    df["Pop_HSH"] = np.select(cond_hsh, [1], default=0)

    # Travesti
    cond_travesti = [
        ((df['st_orgao_genital'] == "Pênis") | (df['st_orgao_genital'] == "Vagina e Pênis")) & (df['co_genero'] == "Travesti"),
        (df['st_orgao_genital'] == "Vagina") & (df['co_genero'] == "Travesti "),
        ((df['tp_sexo_atrib_nasc'] == "Masculino") | (df['tp_sexo_atrib_nasc'] == "Intersexo")) & (df['co_genero'] == "Travesti"),
        (df['co_genero'] == "Travesti")
    ]
    df["Pop_Travesti"] = np.select(cond_travesti, [1, 1, 1, 1], default=0)

    # Mulher Trans
    cond_mulher_trans = [
        ((df['st_orgao_genital'] == "Pênis") | (df['st_orgao_genital'] == "Vagina e Pênis") | (df['tp_sexo_atrib_nasc'] == "Masculino")) &
        ((df['co_genero'] == "Mulher Transexual") | (df['co_genero'] == "Mulher CIS")),
        (df['st_orgao_genital'] == "Pênis") & (df['co_genero'] == "Homem Transexual"),
        ((df['tp_sexo_atrib_nasc'] == "Intersexo") | (df['tp_sexo_atrib_nasc'] == "Feminino")) & (df['co_genero'] == "Mulher Transexual")
    ]
    df["Pop_MulherTrans"] = np.select(cond_mulher_trans, [1, 1, 1], default=0)

    # Homem Trans
    cond_homem_trans = [
        ((df['st_orgao_genital'] == "Vagina") | (df['st_orgao_genital'] == "Vagina e Pênis") | (df['tp_sexo_atrib_nasc'] == "Feminino")) &
        ((df['co_genero'] == "Homem Transexual") | (df['co_genero'] == "Homem CIS")),
        (df['st_orgao_genital'] == "Vagina") & (df['co_genero'] == "Mulher Transexual"),
        ((df['tp_sexo_atrib_nasc'] == "Intersexo") | (df['tp_sexo_atrib_nasc'] == "Masculino")) & (df['co_genero'] == "Homem Transexual")
    ]
    df["Pop_HomemTrans"] = np.select(cond_homem_trans, [1, 1, 1], default=0)

    # Mulher Cis
    cond_mulher_cis = [
        ((df['st_orgao_genital'] == "Vagina") | (df['tp_sexo_atrib_nasc'] == "Feminino") | (df['tp_sexo_atrib_nasc'] == "Intersexo")) &
        (df['co_genero'] == "Mulher CIS")
    ]
    df["Pop_MulherCis"] = np.select(cond_mulher_cis, [1], default=0)

    # Homem Cis Hetero
    cond_homem_cis_hetero = [
        ((df['st_orgao_genital'] == "Pênis") | (df['tp_sexo_atrib_nasc'] == "Masculino") | (df['tp_sexo_atrib_nasc'] == "Intersexo")) &
        (df['co_genero'] == "Homem CIS") &
        (df['co_orientacao_sexual'] == "Heterossexual")
    ]
    df["Pop_HomemCisHetero"] = np.select(cond_homem_cis_hetero, [1], default=0)

    # Não Binário
    cond_nao_binarie = [(df['co_genero'] == "Não binário")]
    df["Pop_NaoBinarie"] = np.select(cond_nao_binarie, [1], default=0)

    # Pop_genero_pratica
    df['Pop_genero_pratica'] = 0
    df.loc[df['Pop_HSH'] == 1, 'Pop_genero_pratica'] = 1
    df.loc[df['Pop_Travesti'] == 1, 'Pop_genero_pratica'] = 2
    df.loc[df['Pop_MulherTrans'] == 1, 'Pop_genero_pratica'] = 3
    df.loc[df['Pop_HomemTrans'] == 1, 'Pop_genero_pratica'] = 4
    df.loc[df['Pop_MulherCis'] == 1, 'Pop_genero_pratica'] = 5
    df.loc[df['Pop_HomemCisHetero'] == 1, 'Pop_genero_pratica'] = 6
    df.loc[df['Pop_NaoBinarie'] == 1, 'Pop_genero_pratica'] = 7

    category_mapping_pop = {
        1: "Gays e outros HSH cis",
        2: "Travestis",
        3: "Mulheres trans",
        4: "Homens trans",
        5: "Mulheres cis",
        6: "Homens heterossexuais cis",
        7: "Não bináries",
    }
    df['Pop_genero_pratica'] = df['Pop_genero_pratica'].map(category_mapping_pop).fillna("Outros")
    
    return df

def enrich_disp_data(df_disp_semdupl, df_cadastro, df_pvha, df_pvha_prim, df_ibge=None):
    """
    Enriquece o dataframe de dispensa com dados de cadastro, UF, Região, Óbito e IBGE.
    """
    if df_disp_semdupl.empty:
        return df_disp_semdupl

    print("Enriquecendo dados de Dispensa...")

    # 1. UF e Região da UDM
    df_disp_semdupl['Cod_IBGE'] = df_disp_semdupl['cod_ibge_udm'].astype(str).str.split('.').str[0]
    df_disp_semdupl['Cod_UF'] = df_disp_semdupl['Cod_IBGE'].str[:2]
    
    df_disp_semdupl['UF_UDM'] = df_disp_semdupl['Cod_UF'].map(UF_MAP).fillna('Error')
    df_disp_semdupl['regiao_UDM'] = df_disp_semdupl['Cod_UF'].map(REGIAO_MAP).fillna('Error')
    
    # 3. Merge com Cadastro
    if not df_cadastro.empty:
        df_disp_semdupl.columns = df_disp_semdupl.columns.str.strip()
        df_cadastro.columns = df_cadastro.columns.str.strip()
        
        print("--- DEBUG MERGE CADASTRO ---")
        
        if 'codigo_pac_eleito' in df_disp_semdupl.columns and 'codigo_pac_eleito' in df_cadastro.columns:
            merge_key = 'codigo_pac_eleito'
        elif 'codigo_paciente' in df_disp_semdupl.columns and 'codigo_paciente' in df_cadastro.columns:
            merge_key = 'codigo_paciente'
        else:
            print("AVISO: Chave de merge não encontrada em ambas as bases.")
            merge_key = None

        if merge_key:
            cols_demograficas = ['st_orgao_genital', 'tp_sexo_atrib_nasc', 'co_genero', 'co_orientacao_sexual', 
                                 'raca_cor', 'escolaridade', 'data_nascimento', 'Cod_unificado']
            
            if merge_key not in cols_demograficas:
                cols_demograficas.append(merge_key)
            
            cols_to_merge = [c for c in cols_demograficas if c in df_cadastro.columns]
            
            # Deduplicar o cadastro pela chave de merge
            df_cad_clean = df_cadastro[cols_to_merge].drop_duplicates(subset=[merge_key])

            # Merge
            df_disp_semdupl = df_disp_semdupl.merge(df_cad_clean, on=merge_key, how='left')
            
            if 'Cod_unificado' in df_disp_semdupl.columns:
                df_disp_semdupl['Cod_unificado'] = df_disp_semdupl['Cod_unificado'].astype('Int64')
            
            # Calcular grupos populacionais APÓS o merge
            df_disp_semdupl = calculate_population_groups(df_disp_semdupl)
        else:
            print("PULANDO merge com Cadastro por falta de chave compatível.")

    # 4. Merge com PVHA (Apenas para consulta, sem filtrar)
    if not df_pvha.empty:
        pvha_sel = df_pvha[['Cod_unificado', 'data_obito', 'PVHA']].copy()
        if 'Cod_unificado' in df_disp_semdupl.columns:
            df_disp_semdupl = df_disp_semdupl.merge(pvha_sel, on='Cod_unificado', how='left')
    
    if not df_pvha_prim.empty:
        prim_sel = df_pvha_prim[['Cod_unificado', 'data_min']].rename(columns={'data_min': 'data_min_PVHA'})
        if 'Cod_unificado' in df_disp_semdupl.columns:
            df_disp_semdupl = df_disp_semdupl.merge(prim_sel, on='Cod_unificado', how='left')

    return df_disp_semdupl

def calculate_intervals(df_disp_semdupl):
    if 'dt_resultado_testagem_hiv' in df_disp_semdupl.columns:
        df_disp_semdupl['dt_resultado_testagem_hiv'] = pd.to_datetime(df_disp_semdupl['dt_resultado_testagem_hiv'], errors='coerce')
        df_disp_semdupl['dt_resultado_hiv'] = df_disp_semdupl['dt_resultado_testagem_hiv'].dt.normalize()
        df_disp_semdupl['dias_teste_disp'] = (df_disp_semdupl['dt_disp'] - df_disp_semdupl['dt_resultado_hiv']).dt.days
    return df_disp_semdupl

def flag_first_last_disp(df_disp_semdupl):
    print("Calculando primeira e última dispensa...")
    df_disp_semdupl['prim_disp'] = (df_disp_semdupl['dt_disp'] == df_disp_semdupl.groupby('codigo_pac_eleito')['dt_disp'].transform('min')).astype(int)
    df_disp_semdupl['ult_disp'] = (df_disp_semdupl['dt_disp'] == df_disp_semdupl.groupby('codigo_pac_eleito')['dt_disp'].transform('max')).astype(int)
    return df_disp_semdupl