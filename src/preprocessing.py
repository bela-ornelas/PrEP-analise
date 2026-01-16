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

def enrich_disp_data(df_disp_semdupl, df_cad_prep, df_cad_hiv, df_pvha, df_pvha_prim, df_ibge=None):
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
    
    # -------------------------------------------------------------------------
    # MERGE 0: Cadastro PrEP (Demográfico) - Para cálculo de populações
    # -------------------------------------------------------------------------
    if not df_cad_prep.empty:
        df_disp_semdupl.columns = df_disp_semdupl.columns.str.strip()
        df_cad_prep.columns = df_cad_prep.columns.str.strip()
        
        # Identificar chave (preferência por codigo_pac_eleito)
        merge_key_prep = 'codigo_pac_eleito' if 'codigo_pac_eleito' in df_cad_prep.columns else 'codigo_paciente'
        
        if merge_key_prep in df_disp_semdupl.columns:
            print(f"Merge Cadastro PrEP (Demográfico) via {merge_key_prep}...")
            cols_demog = ['st_orgao_genital', 'tp_sexo_atrib_nasc', 'co_genero', 'co_orientacao_sexual', 
                          'raca_cor', 'escolaridade', 'data_nascimento']
            if merge_key_prep not in cols_demog: cols_demog.append(merge_key_prep)
            
            # Pega apenas colunas que existem
            cols_to_merge = [c for c in cols_demog if c in df_cad_prep.columns]
            
            # Deduplicar
            df_cad_clean = df_cad_prep[cols_to_merge].drop_duplicates(subset=[merge_key_prep])
            
            df_disp_semdupl = df_disp_semdupl.merge(df_cad_clean, on=merge_key_prep, how='left')
            
            # Calcular populações
            df_disp_semdupl = calculate_population_groups(df_disp_semdupl)

    # -------------------------------------------------------------------------
    # MERGE 1: Cadastro HIV (PVHA) -> Trazer Cod_unificado
    # Chave: codigo_paciente
    # -------------------------------------------------------------------------
    if not df_cad_hiv.empty and 'codigo_paciente' in df_disp_semdupl.columns:
        print("Merge 1: Cadastro HIV (Cod_unificado)...")
        # Garantir tipo compatível
        # df_disp_semdupl['codigo_paciente'] = df_disp_semdupl['codigo_paciente'].astype(str) # Se necessário
        
        cad_hiv_sel = df_cad_hiv[['codigo_paciente', 'Cod_unificado']].drop_duplicates(subset=['codigo_paciente'])
        df_disp_semdupl = df_disp_semdupl.merge(cad_hiv_sel, on='codigo_paciente', how='left')
        
        if 'Cod_unificado' in df_disp_semdupl.columns:
            df_disp_semdupl['Cod_unificado'] = df_disp_semdupl['Cod_unificado'].astype('Int64')

    # -------------------------------------------------------------------------
    # MERGE 2: PVHA Prim (Datas) -> Trazer data_min
    # Chave: Cod_unificado
    # -------------------------------------------------------------------------
    if not df_pvha_prim.empty and 'Cod_unificado' in df_disp_semdupl.columns:
        print("Merge 2: PVHA Prim (Data Diagnóstico)...")
        pvha_prim_sel = df_pvha_prim[['Cod_unificado', 'data_min']].rename(columns={'data_min': 'data_min_PVHA'})
        # Garantir unicidade por Cod_unificado se houver duplicação
        pvha_prim_sel = pvha_prim_sel.drop_duplicates(subset=['Cod_unificado'])
        
        df_disp_semdupl = df_disp_semdupl.merge(pvha_prim_sel, on='Cod_unificado', how='left')

    # -------------------------------------------------------------------------
    # MERGE 3: PVHA (Óbito/Status) -> Trazer data_obito, PVHA
    # Chave: Cod_unificado
    # -------------------------------------------------------------------------
    if not df_pvha.empty and 'Cod_unificado' in df_disp_semdupl.columns:
        print("Merge 3: PVHA (Óbito/Status)...")
        pvha_sel = df_pvha[['Cod_unificado', 'data_obito', 'PVHA']].copy()
        pvha_sel = pvha_sel.drop_duplicates(subset=['Cod_unificado'])
        
        df_disp_semdupl = df_disp_semdupl.merge(pvha_sel, on='Cod_unificado', how='left')

    # -------------------------------------------------------------------------
    # MERGE 4: Tabela IBGE -> Trazer nome_mun
    # Chave: cod_ibge_udm (no Disp) == Cod_mun_7 (na Tabela)
    # -------------------------------------------------------------------------
    if df_ibge is not None and not df_ibge.empty:
        print("Merge 4: Tabela IBGE (Município)...")
        # Preparar tabela auxiliar
        ibge_sel = df_ibge[['Cod_mun_7', 'nome_mun']].rename(columns={'nome_mun': 'nome_mun_udm'})
        
        # Garantir tipos compatíveis (converter para numérico ou string em ambos)
        # Assumindo numérico
        df_disp_semdupl['cod_ibge_udm'] = pd.to_numeric(df_disp_semdupl['cod_ibge_udm'], errors='coerce')
        ibge_sel['Cod_mun_7'] = pd.to_numeric(ibge_sel['Cod_mun_7'], errors='coerce')
        
        df_disp_semdupl = df_disp_semdupl.merge(
            ibge_sel, 
            left_on='cod_ibge_udm', 
            right_on='Cod_mun_7', 
            how='left'
        )

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