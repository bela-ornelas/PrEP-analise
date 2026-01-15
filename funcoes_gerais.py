"""
Programa com funções gerais de tratamento de bases de dados.

Arquivo: funcoes_gerais.py

Descrição: Um programa Python com as principais funções de rotina para tratamento de bases de dados.

Autor: Tiago Benoliel - Assessoria de Monitoramento e Avaliação (AMA)
Organização: Departamento de HIV/Aids, Tuberculose, Hepatites Virais e ISTs (DATHI) - Ministério da Saúde

Data de Criação: 15/05/2024
Versão: 1.0.0
Repositório GitHub: [https://github.com/tbenoliel/Monitoramento-Clinico-HIV]
"""


import numpy as np 
import pandas as pd
from IPython.display import display
import datetime
import matplotlib.pyplot as plt
import math
import statsmodels.api as sm
import pymannkendall as mk
from scipy.stats import shapiro, levene, wilcoxon, ttest_1samp, ttest_ind, chi2_contingency, mannwhitneyu
from sklearn.linear_model import LinearRegression
from statsmodels.regression.linear_model import yule_walker
from sklearn.metrics import r2_score
import prince
import plotly.express as px
import seaborn as sns
from sklearn.utils import resample
from statstests.tests import shapiro_francia
import time
import re
import sys, os
from contextlib import contextmanager



@contextmanager
def suprimir_output():
    """Contexto para silenciar prints e warnings no bloco interno."""
    with open(os.devnull, 'w') as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr



def idade_cat(DF:pd.DataFrame, data_ref:str, data_nasc:str = "data_nascimento", faixas_etarias=None):

    """
    Calcula a idade entre as datas em duas colunas de um DataFrame, criando nova coluna
    com a idade nas faixas etárias especificadas.
    

    Parameters
    ----------
    DF: DataFrame com a base a ser analisada.

    data_ref: String - Coluna com a data de referência da idade (Data da dispensa, do exame...)

    data_nasc: String - Coluna com a data de base nascimento. Default = "data_nascimento".

    faixas_etarias: Lista de tuplas, onde cada tupla representa uma faixa etária no formato (limite_inferior, limite_superior).
    O limite inferior é incluido na categoria (>=) e o limite superior não é incluido (<).
        Se MCantigo, utiliza as faixas etárias padrão do monitoramento clínico antigo.   

            < 2 anos
            2 a 4 anos
            5 a 8 anos
            9 a 11 anos
            12 a 17 anos
            18 a 24 anos
            25 a 29 anos
            30 a 49 anos
            50 anos ou mais
        
        Se "spectrum1", utiliza as faixas etárias padrão do Spectrum.

            "0 a 4 anos",
            "5 a 9 anos",
            "10 a 14 anos",
            "15 a 19 anos",
            "20 a 24 anos",
            "25 a 49 anos",
            "50 anos ou mais"
    
        Se "spectrum2", utiliza as faixas etárias padrão do Spectrum 2.

            "0 a 4 anos",
            "5 a 9 anos",
            "10 a 14 anos",
            "15 a 19 anos",
            "20 a 24 anos",
            "25 a 29 anos",
            "30 a 34 anos",
            "35 a 39 anos",
            "40 a 44 anos",
            "45 a 49 anos",
            "50 a 54 anos",
            "55 a 59 anos",
            "60 a 64 anos",
            "65 a 69 anos",
            "70 a 74 anos",
            "75 a 79 anos",
            "80 anos ou mais"

        Se "spectrum_crianca", utiliza as faixas etárias padrão do Spectrum para Crianças.

            "0 a 14 anos",
            "15 anos ou mais"

    
    
    """

    if faixas_etarias is None:
        faixas_etarias = [
            (0, 13),
            (13, 18),
            (18, 25),
            (25, 40),
            (40, 60),
            (60, 99)
        ]

    elif faixas_etarias == "MC_antigo":
        faixas_etarias = [
            (0, 2),
            (2, 5),
            (5, 9),
            (9, 12),
            (12, 18),
            (18, 25),
            (25, 30),
            (30, 50),
            (50, 99)
        ]

    elif faixas_etarias == "spectrum1":
        faixas_etarias = [
            (0, 5),
            (5, 10),
            (10, 15),
            (15, 20),
            (20, 25),
            (25, 50),
            (50, 99)
        ]

    elif faixas_etarias == "spectrum2":
        faixas_etarias = [
            (0, 5),
            (5, 10),
            (10, 15),
            (15, 20),
            (20, 25),
            (25, 30),
            (30, 35),
            (35, 40),
            (40, 45),
            (45, 50),
            (50, 55),
            (55, 60),
            (60, 65),
            (65, 70),
            (70, 75),
            (75, 80),
            (80, 99)
        ]

    elif faixas_etarias == "SAGE":
        faixas_etarias = [
            (0, 5),
            (5, 10),
            (10, 15),
            (15, 20),
            (20, 25),
            (25, 30),
            (30, 35),
            (35, 40),
            (40, 45),
            (45, 50),
            (50, 55),
            (55, 60),
            (60, 99)
        ]

    elif faixas_etarias == "spectrum_crianca":
        faixas_etarias = [
            (0, 15),
            (15, 99)
        ]

    elif faixas_etarias == "Hep1":
        faixas_etarias = [
            (0, 3),
            (3, 6),
            (6, 12),
            (12, 20),
            (20, 30),
            (30, 40),
            (40, 50),
            (50, 60),
            (60, 70),
            (70, 99)
        ]

    elif faixas_etarias == "Hep2":
        faixas_etarias = [
            (0, 20),
            (20, 30),
            (30, 40),
            (40, 50),
            (50, 60),
            (60, 70),
            (70, 99)
        ]

    elif faixas_etarias == "Hep3":
        faixas_etarias = [
            (0, 30),
            (30, 50),
            (50, 99)
        ]

    DF[data_ref] = pd.to_datetime(DF[data_ref],errors='coerce')
    DF[data_nasc] = pd.to_datetime(DF[data_nasc],errors='coerce')
    DF[data_ref] = DF[data_ref].dt.normalize()
    DF[data_nasc] = DF[data_nasc].dt.normalize()
    
    DF[f"Idade_{data_ref}"] = (DF[data_ref] - DF[data_nasc]).dt.days/365

    Cond_idadecat = []
    Idade_escolhacat = []

    for limite_inferior, limite_superior in faixas_etarias:
        Cond_idadecat.append((DF[f"Idade_{data_ref}"] >= limite_inferior) & (DF[f"Idade_{data_ref}"] < limite_superior))
        Idade_escolhacat.append(f"{limite_inferior} a {limite_superior-1} anos")
    Idade_escolhacat[0] = f"Menos de {faixas_etarias[0][1]} anos"
    Idade_escolhacat[-1] = f"Mais de {limite_inferior} anos"
    return np.select(Cond_idadecat, Idade_escolhacat, default = "Não Informado")



def TARV(DF:pd.DataFrame, col_data_ref:str, col_dt_disp:str, col_duracao:str = "duracao_sum"):
    DF["dt_lim_prox_disp_temp"] = DF[col_dt_disp] + pd.to_timedelta(DF[col_duracao], unit="D")
    DF["dt_lim_prox_disp_temp"] = pd.to_datetime(DF["dt_lim_prox_disp_temp"], errors="coerce")
    DF["dt_lim_prox_disp_temp"] = DF["dt_lim_prox_disp_temp"].dt.normalize()
    DF["Atraso_temp"] = (DF[col_data_ref] - DF["dt_lim_prox_disp_temp"]).dt.days
    return np.where(DF["Atraso_temp"] <= 60, "Tarv", "Interrompido")



def ajuste_sexo_nome(x):
    x = str(x).strip()
    cond = [(x == "M") | (x == "1") | (x == "1.0") | (x == "Homem"),
            (x == "F") | (x == "2") | (x == "2.0") | (x == "Mulher")]
    retorno = ["Homem", "Mulher"]
    return np.select(cond,retorno, default = None)



def tabela_freq(x:pd.DataFrame,y:str, total:str = "Total"):
    """
    Função que gera uma tabela com os dados de frequência de uma coluna de DataFrame. Simula o Tab_freq do SPSS.
    
    Parameters
    ----------    
    x: DataFrame com os dados.
    y: String - Nome da coluna a ser analisada
    total: Nome da coluna que será gerada com a soma total.
    
    """
    df = pd.DataFrame(x[y].value_counts(dropna = False).sort_index())
    df["Freq_Val"] = pd.DataFrame(x[y].value_counts(dropna = True).sort_index())
    df["Freq_Rel"] = pd.DataFrame((x[y].value_counts(normalize = True, dropna = False)*100).round(2).sort_index())
    df["Freq_Rel_Val"] = pd.DataFrame((x[y].value_counts(normalize = True)*100).round(2).sort_index())
    soma = df.sum()
    soma.name = total
    df = pd.concat([df, pd.DataFrame(soma).T], axis=0)  # Substitui a linha df = df.append(soma) 
    df["Freq_Rel_Acum"] = pd.DataFrame((x[y].value_counts(normalize = True)*100).sort_index().cumsum().round(2))
    df.rename(columns = {"count":y}, inplace = True)
    return df



def ajusta_data_linha_vetorizado(df:pd.DataFrame,
                                 coluna_data:str,
                                 coluna_retorno:str,
                                 ano_esperado: int | None = None):

    # Garantir que a coluna 'data' seja uma string
    df[coluna_data] = df[coluna_data].apply(lambda x: str(x).strip())

    # Lista de formatos de data e regex correspondentes
    formatos = [
        # yyyy-mm-dd com variações
        ('%Y-%m-%d %H:%M:%S.%f', r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3,6}$'),
        ('%Y-%m-%d %H:%M:%S',     r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'),
        ('%Y-%m-%d %H:%M',        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$'),
        ('%Y-%m-%d',              r'^\d{4}-\d{2}-\d{2}$'),

        # yyyy/mm/dd com variações
        ('%Y/%m/%d %H:%M:%S.%f',  r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3,6}$'),
        ('%Y/%m/%d %H:%M:%S',     r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$'),
        ('%Y/%m/%d %H:%M',        r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}$'),
        ('%Y/%m/%d',              r'^\d{4}/\d{2}/\d{2}$'),

        # dd/mm/yyyy e dd-mm-yyyy (muito comuns em ETL)
        ('%d/%m/%Y %H:%M:%S',     r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$'),
        ('%d/%m/%Y %H:%M',        r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$'),
        ('%d/%m/%Y',              r'^\d{2}/\d{2}/\d{4}$'),

        ('%d-%m-%Y %H:%M:%S',     r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}$'),
        ('%d-%m-%Y %H:%M',        r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$'),
        ('%d-%m-%Y',              r'^\d{2}-\d{2}-\d{4}$'),

        # Sem separador
        ('%Y%m%d',                r'^\d{8}$'),       # yyyyMMdd
        ('%d%m%Y',                r'^\d{8}$'),       # ddMMyyyy

        # ISO 8601 parcial
        ('%Y-%m-%dT%H:%M:%S.%f',  r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,6}$'),
        ('%Y-%m-%dT%H:%M:%S',     r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$')
    ]
    
    # Inicializando uma coluna com valores nulos
    df[coluna_retorno] = pd.NaT

    # Para cada formato, tente converter as datas correspondentes
    for fmt, regex in formatos:
        # Só tenta para linhas ainda não parseadas
        mask_base = df[coluna_retorno].isna()
        mask_regex = df[coluna_data].str.match(regex)
        mask = mask_base & mask_regex

        if not mask.any():
            continue
        
        parsed = pd.to_datetime(
            df.loc[mask, coluna_data],
            format=fmt,
            errors='coerce'
        )
        if ano_esperado is not None:
            parsed = parsed.where(parsed.dt.year == ano_esperado, pd.NaT)

        df.loc[mask, coluna_retorno] = parsed.dt.normalize()
    
    return df



def padronizar_variaveis_vetorizado(DF:pd.DataFrame, var:str, col_codigo_uni:str = 'Cod_unificado', col_data_ref:str = 'data_ref', funcao:str = "moda", mais_antigo:bool = True):
    
    if funcao.strip().lower() == "max":
        # Para cada variável da lista, calcule o maior valor
        moda_por_grupo = DF.groupby(col_codigo_uni)[var].agg("max")

    elif funcao.strip().lower() == "min":
        # Para cada variável da lista, calcule o menor valor
        moda_por_grupo = DF.groupby(col_codigo_uni)[var].agg("min")

    else:
        DF = DF.sort_values(by=[col_codigo_uni, col_data_ref], ascending = mais_antigo)
        # Para cada variável da lista, calcule a moda e resolva o empate
        moda_por_grupo = DF.groupby(col_codigo_uni)[var].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

    # Atribui a moda diretamente aos grupos
    DF[var] = DF[col_codigo_uni].map(moda_por_grupo)
    
    return DF



def limpa_texto(texto):
    """
    Remove palavras comuns e limpa espaços extras ao mesmo tempo
    """

    palavras_comuns = ["da","do","de", "das","dos","des","d","e","a","iiigt","iigt","gmii","tjmb"]
    
    if isinstance(texto, str):
        # Remove sequências de 'z' repetidas
        texto = re.sub(r'zz+', '', texto)
        texto = re.sub(r'zzz+', '', texto)
        # Remove sequências de 'x' repetidas
        texto = re.sub(r'xx+', '', texto)
        texto = re.sub(r'xxx+', '', texto)
        # Remove caracteres não alfabéticos, mantendo espaços
        texto = re.sub(r'[^a-zA-Z\s]', '', texto)
        # Divide o texto em palavras
        palavras = texto.split()
        # Remove palavras comuns
        palavras = [palavra for palavra in palavras if palavra.lower() not in palavras_comuns]
        # Remove palavras com apenas um caractere
        palavras_filtradas = [palavra for palavra in palavras if len(palavra) > 1]
        # Junta as palavras filtradas de volta em uma string
        return ' '.join(palavras_filtradas)
    else:
        return texto



def contar_comparacoes(linha, colunas_1, colunas_2):
    """
    # Função que conta quantas comparações são verdadeiras

    """
    comparacoes = [
        linha[colunas_1[0]] == linha[colunas_2[0]],
        linha[colunas_1[1]] == linha[colunas_2[1]],
        linha[colunas_1[2]] == linha[colunas_2[2]]
    ]
    return sum(comparacoes)



def Na_linha(DF:pd.DataFrame, lista_colunas:list, col_data:str, cod_indent:str, n:int = 10):
    
    """
    Retorna um DataFrame com os últimos n procedimentos (exames, dispensas...) da pessoa
    em colunas numeradas em uma única linha por pessoa. Retorna também o primeiro evento conhecido (_Prim).
        
    Parameters
    ----------
    DF : DataFrame com cada procedimento realizado em uma linha diferente

    lista_colunas : lista -  liste os nomes (strig) das colunas que contem as informações que deseja buscar

    col_data : string -  o nome da coluna que contem a data do evento que deseja buscar.

    cod_indent: string - o nome da coluna que contem o código identificador da pessoa.

    n : int - número de procedimentos anteriores a buscar, default 10.
    
    """
    DF[col_data] = pd.to_datetime(DF[col_data],errors='coerce')
    DF[col_data] = DF[col_data].dt.normalize()
    DF.sort_values(by = [cod_indent,col_data], ascending = [True, False], inplace = True)
    DF.reset_index(drop = True, inplace = True)
    
    DF[f"{col_data}_Prim"] = DF.groupby([cod_indent])[col_data].transform('last')
    
    for c in lista_colunas:
        DF[f"{c}_Prim"] = DF.groupby([cod_indent])[c].transform('last')

    for i in range(n):
        DF[f"{col_data}_{i}"] = DF.groupby([cod_indent])[col_data].shift(-i)
            
        for c in lista_colunas:
            DF[f"{c}_{i}"] = DF.groupby([cod_indent])[c].shift(-i)

    
    DF_ult = DF.drop_duplicates(cod_indent, keep = "first").copy()
            
    return DF_ult



def encontrar_menor_data_vetorizado(df:pd.DataFrame, colunas_datas:list, nome_dt_min:str = 'data_min'):
    """
    Essa função encontra a menor data entre várias colunas de datas em um DataFrame e cria uma nova coluna com a menor data encontrada.

    Parameters
    ----------
    df : pd.DataFrame
        O DataFrame contendo as colunas de datas.
        
    colunas_datas : list
        Lista de strings representando os nomes das colunas de datas a serem consideradas para encontrar a menor data.
        
    nome_dt_min : str, opcional
        O nome para a nova coluna que conterá a menor data encontrada. O padrão é 'data_min'.

    Returns
    -------
    pd.DataFrame
        O DataFrame original com uma nova coluna contendo a menor data encontrada.
    """

    datas = df[colunas_datas].apply(pd.to_datetime, errors='coerce')
    
    # Exclude rows with all NaT before idxmin
    not_all_nat = ~datas.isna().all(axis=1)
    menor_data = datas[not_all_nat].min(axis=1)
    origem_data_min = datas[not_all_nat].idxmin(axis=1)
    
    # Create a Series with NaT for missing values
    missing_nat_series = pd.Series(pd.NaT, index=df.loc[~not_all_nat].index)
    
    # Concatenate origem_data_min with missing_nat_series
    origem_data_min = pd.concat([origem_data_min, missing_nat_series])
    
    df[nome_dt_min] = pd.concat([menor_data, pd.Series(pd.NaT, index=df.loc[~not_all_nat].index)])
    df[f'origem_{nome_dt_min}'] = origem_data_min
    
    return df



def encontrar_maior_data_vetorizado(df:pd.DataFrame, colunas_datas:list, nome_dt_max:str = 'data_max'):
    """
    Essa função encontra a menor data entre várias colunas de datas em um DataFrame e cria uma nova coluna com a maior data encontrada.

    Parameters
    ----------
    df : pd.DataFrame
        O DataFrame contendo as colunas de datas.
        
    colunas_datas : list
        Lista de strings representando os nomes das colunas de datas a serem consideradas para encontrar a maior data.
        
    nome_dt_min : str, opcional
        O nome para a nova coluna que conterá a maior data encontrada. O padrão é 'data_max'.

    Returns
    -------
    pd.DataFrame
        O DataFrame original com uma nova coluna contendo a maior data encontrada.
    """

    datas = df[colunas_datas].apply(pd.to_datetime, errors='coerce')
    
    # Exclude rows with all NaT before idxmax
    not_all_nat = ~datas.isna().all(axis=1)
    maior_data = datas[not_all_nat].max(axis=1)
    origem_data_max = datas[not_all_nat].idxmax(axis=1)
    
    # Create a Series with NaT for missing values
    missing_nat_series = pd.Series(pd.NaT, index=df.loc[~not_all_nat].index)
    
    # Concatenate origem_data_min with missing_nat_series
    origem_data_max = pd.concat([origem_data_max, missing_nat_series])
    
    df[nome_dt_max] = pd.concat([maior_data, pd.Series(pd.NaT, index=df.loc[~not_all_nat].index)])
    df[f'origem_{nome_dt_max}'] = origem_data_max
    
    return df



def ibge_resid(DF:pd.DataFrame,col_ibge_resid:str = "codigo_ibge_resid", fill_na:bool = True,
            cols_ibge:list = ["cod_ibge_udm","cod_ibge_solicitante_cv","cod_ibge_solicitante_cd4"],
            caminho_ibge:str = "//SAP109/Bancos AMA/2024/IBGE/Mun_ibge.xlsx"):

    """
    Essa função atualiza a coluna de código IBGE de residência em um DataFrame, preenche valores ausentes com outras colunas de códigos IBGE e cria novas colunas indicando a capital, UF e região.

    Parameters
    ----------
    DF : pd.DataFrame
        O DataFrame contendo as colunas de códigos IBGE.
        
    col_ibge_resid : str, opcional
        O nome da coluna de código IBGE de residência. O padrão é "codigo_ibge_resid".
        
    fill_na : bool, opcional
        Indica se os valores ausentes na coluna de código IBGE de residência devem ser preenchidos com valores de outras colunas de códigos IBGE. O padrão é True.
        
    cols_ibge : list, opcional
        Lista de strings representando os nomes das colunas de códigos IBGE que podem ser usadas para preencher valores ausentes na coluna de código IBGE de residência. O padrão é ["cod_ibge_udm", "cod_ibge_solicitante_cv", "cod_ibge_solicitante_cd4"].

    Returns
    -------
    pd.DataFrame
        O DataFrame original com as colunas atualizadas e as novas colunas indicando a capital, UF e região.
    """

    if fill_na is True:
        for col in cols_ibge:
            DF[col_ibge_resid] = DF[col_ibge_resid].fillna(DF[col])

    DF[col_ibge_resid] = pd.to_numeric(DF[col_ibge_resid], errors='coerce')

    DF["cod_ibge6_res"] = DF[col_ibge_resid].apply(lambda x:str(x)[:6] if pd.notna(x) else np.nan)


    Cond_cap = [
        (DF["cod_ibge6_res"] == "110020"),
        (DF["cod_ibge6_res"] == "130260"),
        (DF["cod_ibge6_res"] == "120040"),
        (DF["cod_ibge6_res"] == "500270"),
        (DF["cod_ibge6_res"] == "160030"),
        (DF["cod_ibge6_res"] == "530010"),
        (DF["cod_ibge6_res"] == "140010"),
        (DF["cod_ibge6_res"] == "510340"),
        (DF["cod_ibge6_res"] == "172100"),
        (DF["cod_ibge6_res"] == "355030"),
        (DF["cod_ibge6_res"] == "221100"),
        (DF["cod_ibge6_res"] == "330455"),
        (DF["cod_ibge6_res"] == "150140"),
        (DF["cod_ibge6_res"] == "520870"),
        (DF["cod_ibge6_res"] == "292740"),
        (DF["cod_ibge6_res"] == "420540"),
        (DF["cod_ibge6_res"] == "211130"),
        (DF["cod_ibge6_res"] == "270430"),
        (DF["cod_ibge6_res"] == "431490"),
        (DF["cod_ibge6_res"] == "410690"),
        (DF["cod_ibge6_res"] == "310620"),
        (DF["cod_ibge6_res"] == "230440"),
        (DF["cod_ibge6_res"] == "261160"),
        (DF["cod_ibge6_res"] == "250750"),
        (DF["cod_ibge6_res"] == "280030"),
        (DF["cod_ibge6_res"] == "240810"),
        (DF["cod_ibge6_res"] == "320530")]


    cap_escolha = ["Porto Velho","Manaus","Rio Branco", "Campo Grande",
                "Macapá", "Brasília", "Boa Vista", "Cuiabá", "Palmas",
                "São Paulo", "Teresina", "Rio de Janeiro", "Belém", "Goiânia",
                "Salvador", "Florianópolis", "São Luís", "Maceió",
                "Porto Alegre", "Curitiba", "Belo Horizonte", "Fortaleza", 
                "Recife", "João Pessoa", "Aracaju", "Natal", "Vitória"]



    DF["capital_res"] = np.select(Cond_cap, cap_escolha, default = None)
    display(pd.DataFrame(DF["capital_res"].value_counts()))
    print()

    Cond_uf = [
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "11"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "13"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "12"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "50"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "16"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "53"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "14"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "51"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "17"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "35"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "22"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "33"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "15"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "52"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "29"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "42"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "21"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "27"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "43"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "41"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "31"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "23"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "26"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "25"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "28"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "24"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:2]) == "32")]


    uf_escolha = ["RO","AM","AC", "MS",
                "AP", "DF", "RR", "MT", "TO",
                "SP", "PI", "RJ", "PA", "GO",
                "BA", "SC", "MA", "AL",
                "RS", "PR", "MG", "CE", 
                "PE", "PB", "SE", "RN", "ES"]



    DF["uf_res"] = np.select(Cond_uf, uf_escolha, default = None)
    display(pd.DataFrame(DF["uf_res"].value_counts()))
    print()

    Cond_reg = [
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:1]) == "1"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:1]) == "5"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:1]) == "3"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:1]) == "2"),
        (DF["cod_ibge6_res"].apply(lambda x:str(x)[0:1]) == "4")
    ]


    reg_escolha = [
        "Norte",
        "Centro-Oeste",
        "Sudeste",
        "Nordeste",
        "Sul"
    ]

    DF["reg_res"] = np.select(Cond_reg, reg_escolha, default = None)
    display(pd.DataFrame(DF["reg_res"].value_counts()))
    print()

    ibge = pd.read_excel(caminho_ibge)

    ibge.rename(columns={"Nome_mun":"Nome_mun_resid","Populacao":"Populacao_resid"}, inplace=True)

    ibge["cod_ibge6_res"] = ibge[col_ibge_resid].apply(lambda x:str(x)[:6] if pd.notna(x) else np.nan)

    DF = DF.drop(columns=[col_ibge_resid])

    DF = pd.merge(DF,ibge[["cod_ibge6_res","Nome_mun_resid","Populacao_resid",col_ibge_resid]], how = "left", on = "cod_ibge6_res")

    return DF



def ibge_inst_sol_exames(DF:pd.DataFrame, fill_na:bool = True,
            col_cod_ibge_udm:str = "cod_ibge_udm", col_cod_ibge_solicitante_cv:str = "cod_ibge_solicitante_cv",
            col_cod_ibge_solicitante_cd4 = "cod_ibge_solicitante_cd4", col_nome_inst_sol_cv:str = "nm_inst_sol_cv",
            col_nome_inst_sol_cd4:str = "nm_inst_sol_cd4",col_ibge_resid:str = "codigo_ibge_resid", 
            cols_sinan:list = ["ID_MUNICIP_Ad","ID_MUNICIP_cong","ID_MUNICIP_gest", "ID_MUNICIP_cr", "ID_MN_RESI_Ad","ID_MN_RESI_cong","ID_MN_RESI_gest","ID_MN_RESI_cr","CODMUNOCOR","CODMUNCART","CODMUNRES"],
            caminho_ibge:str = "//SAP109/Bancos AMA/2024/IBGE/Mun_ibge.xlsx"):

    """
    Essa função atualiza a coluna de código IBGE e de nome da instituição solicitante de CV em um DataFrame e preenche valores ausentes com o valor da instituição solicitante de CD4.
    Os valores de IBGE que continuarem em branco, receberão o código IBGE da UDM e por último o de residência. O nome das instituições que ficarem em branco, receberão o valor "Sem exames no SUS"

    Parameters
    ----------
    DF : pd.DataFrame
        O DataFrame contendo as colunas de códigos IBGE.
        
    col_ibge_resid : str, opcional
        O nome da coluna de código IBGE de residência. O padrão é "codigo_ibge_resid".
        
    fill_na : bool, opcional
        Indica se os valores ausentes na coluna de código IBGE de exames devem ser preenchidos com valores de IBGE da UDM e de residência. O padrão é True.

    Returns
    -------
    pd.DataFrame
        O DataFrame original com as colunas atualizadas.
    """
    DF["ibge_inst_exames"] = DF[col_cod_ibge_solicitante_cv].fillna(DF[col_cod_ibge_solicitante_cd4])


    DF["nome_inst_exames"] = DF[col_nome_inst_sol_cv].fillna(DF[col_nome_inst_sol_cd4])
    DF["nome_inst_exames"] = DF["nome_inst_exames"].fillna("SEM EXAMES NO SUS")

    if fill_na is True:
        DF["ibge_inst_exames"] = DF["ibge_inst_exames"].fillna(DF[col_cod_ibge_udm])
        DF["ibge_inst_exames"] = DF["ibge_inst_exames"].fillna(DF[col_ibge_resid])
        for col_sinan in cols_sinan:
            if col_sinan in DF.columns:
                DF["ibge_inst_exames"] = DF["ibge_inst_exames"].fillna(DF[col_sinan])

    DF["ibge_inst_exames"] = pd.to_numeric(DF["ibge_inst_exames"], errors='coerce')


    Cond_uf = [
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "11"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "13"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "12"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "50"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "16"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "53"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "14"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "51"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "17"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "35"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "22"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "33"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "15"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "52"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "29"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "42"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "21"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "27"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "43"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "41"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "31"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "23"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "26"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "25"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "28"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "24"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "32")]


    uf_escolha = ["RO","AM","AC", "MS",
                "AP", "DF", "RR", "MT", "TO",
                "SP", "PI", "RJ", "PA", "GO",
                "BA", "SC", "MA", "AL",
                "RS", "PR", "MG", "CE", 
                "PE", "PB", "SE", "RN", "ES"]



    DF["uf_inst"] = np.select(Cond_uf, uf_escolha, default = None)
    display(pd.DataFrame(DF["uf_inst"].value_counts()))
    print()

    Cond_uf = [
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "11"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "13"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "12"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "50"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "16"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "53"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "14"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "51"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "17"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "35"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "22"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "33"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "15"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "52"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "29"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "42"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "21"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "27"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "43"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "41"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "31"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "23"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "26"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "25"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "28"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "24"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:2]) == "32")]


    uf_escolha = ["Rondônia","Amazonas","Acre", "Mato Grosso do Sul",
                "Amapá", "Distrito Federal", "Roraima", "Mato Grosso", "Tocantins",
                "São Paulo", "Piauí", "Rio de Janeiro", "Pará", "Goiás",
                "Bahia", "Santa Catarina", "Maranhão", "Alagoas",
                "Rio Grande do Sul", "Paraná", "Minas Gerais", "Ceará", 
                "Pernambuco", "Paraíba", "Sergipe", "Rio Grande do Norte", "Espírito Santo"]



    DF["uf_inst_completo"] = np.select(Cond_uf, uf_escolha, default = None)
    display(pd.DataFrame(DF["uf_inst_completo"].value_counts()))
    print()

    Cond_reg = [
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:1]) == "1"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:1]) == "5"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:1]) == "3"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:1]) == "2"),
        (DF["ibge_inst_exames"].apply(lambda x:str(x)[0:1]) == "4")
    ]


    reg_escolha = [
        "Norte",
        "Centro-Oeste",
        "Sudeste",
        "Nordeste",
        "Sul"
    ]

    DF["reg_inst"] = np.select(Cond_reg, reg_escolha, default = None)
    display(pd.DataFrame(DF["reg_inst"].value_counts()))
    print()

    DF["ibge_inst_exames"] = pd.to_numeric(DF['ibge_inst_exames'], errors='coerce')

    DF["cod_ibge6_exame"] = DF["ibge_inst_exames"].apply(lambda x:str(x)[:6] if pd.notna(x) else np.nan)

    ibge = pd.read_excel(caminho_ibge)

    ibge.rename(columns={col_ibge_resid:"ibge_inst_exames", "Nome_mun":"Nome_mun_exame",
                         "Populacao":"Populacao_exame"}, inplace=True)
    
    ibge["cod_ibge6_exame"] = ibge["ibge_inst_exames"].apply(lambda x:str(x)[:6] if pd.notna(x) else np.nan)

    DF = DF.drop(columns=["ibge_inst_exames"])

    DF = pd.merge(DF,ibge[["cod_ibge6_exame","ibge_inst_exames","Nome_mun_exame","Populacao_exame"]], how = "left", on = "cod_ibge6_exame")

    DF["ibge_inst_exames"] = pd.to_numeric(DF['ibge_inst_exames'], errors='coerce')

    return DF



def ibge_organizacao(DF:pd.DataFrame,col_ibge_ref:str, fill_na:bool = False,
            cols_ibge:list = [], sufix:str = ""):

    """
    Essa função atualiza a coluna de código IBGE de residência em um DataFrame, preenche valores ausentes com outras colunas de códigos IBGE e cria novas colunas indicando a capital, UF e região.

    Parameters
    ----------
    DF : pd.DataFrame
        O DataFrame contendo as colunas de códigos IBGE.
        
    col_ibge_ref : str,
        O nome da coluna de código IBGE de referência.
        
    fill_na : bool, padrão False
        Indica se os valores ausentes na coluna de código IBGE de referência devem ser preenchidos com valores de outras colunas de códigos IBGE. O padrão é False.
        
    cols_ibge : list, opcional
        Lista de strings representando os nomes das colunas de códigos IBGE que podem ser usadas para preencher valores ausentes na coluna de código IBGE de residência.

    sufix : str, opcional
        Sufixo a ser adicionado às novas colunas criadas.

    Returns
    -------
    pd.DataFrame
        O DataFrame original com as colunas atualizadas e as novas colunas indicando a capital, UF e região.
    """

    if fill_na is True:
        for col in cols_ibge:
            DF[col_ibge_ref] = DF[col_ibge_ref].fillna(DF[col])

    DF[col_ibge_ref] = pd.to_numeric(DF[col_ibge_ref], errors='coerce')


    Cond_cap = [
        (DF[col_ibge_ref] == 1100205),
        (DF[col_ibge_ref] == 1302603),
        (DF[col_ibge_ref] == 1200401),
        (DF[col_ibge_ref] == 5002704),
        (DF[col_ibge_ref] == 1600303),
        (DF[col_ibge_ref] == 5300108),
        (DF[col_ibge_ref] == 1400100),
        (DF[col_ibge_ref] == 5103403),
        (DF[col_ibge_ref] == 1721000),
        (DF[col_ibge_ref] == 3550308),
        (DF[col_ibge_ref] == 2211001),
        (DF[col_ibge_ref] == 3304557),
        (DF[col_ibge_ref] == 1501402),
        (DF[col_ibge_ref] == 5208707),
        (DF[col_ibge_ref] == 2927408),
        (DF[col_ibge_ref] == 4205407),
        (DF[col_ibge_ref] == 2111300),
        (DF[col_ibge_ref] == 2704302),
        (DF[col_ibge_ref] == 4314902),
        (DF[col_ibge_ref] == 4106902),
        (DF[col_ibge_ref] == 3106200),
        (DF[col_ibge_ref] == 2304400),
        (DF[col_ibge_ref] == 2611606),
        (DF[col_ibge_ref] == 2507507),
        (DF[col_ibge_ref] == 2800308),
        (DF[col_ibge_ref] == 2408102),
        (DF[col_ibge_ref] == 3205309)]


    cap_escolha = ["Porto Velho","Manaus","Rio Branco", "Campo Grande",
                "Macapá", "Brasília", "Boa Vista", "Cuiabá", "Palmas",
                "São Paulo", "Teresina", "Rio de Janeiro", "Belém", "Goiânia",
                "Salvador", "Florianópolis", "São Luís", "Maceió",
                "Porto Alegre", "Curitiba", "Belo Horizonte", "Fortaleza", 
                "Recife", "João Pessoa", "Aracaju", "Natal", "Vitória"]



    DF[f"capital_{sufix}"] = np.select(Cond_cap, cap_escolha, default = None)
    display(pd.DataFrame(DF[f"capital_{sufix}"].value_counts()))
    print()

    Cond_uf = [
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "11"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "13"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "12"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "50"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "16"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "53"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "14"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "51"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "17"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "35"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "22"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "33"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "15"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "52"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "29"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "42"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "21"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "27"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "43"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "41"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "31"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "23"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "26"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "25"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "28"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "24"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:2]) == "32")]


    uf_escolha = ["RO","AM","AC", "MS",
                "AP", "DF", "RR", "MT", "TO",
                "SP", "PI", "RJ", "PA", "GO",
                "BA", "SC", "MA", "AL",
                "RS", "PR", "MG", "CE", 
                "PE", "PB", "SE", "RN", "ES"]



    DF[f"uf_{sufix}"] = np.select(Cond_uf, uf_escolha, default = None)
    display(pd.DataFrame(DF[f"uf_{sufix}"].value_counts()))
    print()

    Cond_reg = [
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:1]) == "1"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:1]) == "5"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:1]) == "3"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:1]) == "2"),
        (DF[col_ibge_ref].apply(lambda x:str(x)[0:1]) == "4")
    ]


    reg_escolha = [
        "Norte",
        "Centro-Oeste",
        "Sudeste",
        "Nordeste",
        "Sul"
    ]

    DF[f"reg_{sufix}"] = np.select(Cond_reg, reg_escolha, default = None)
    display(pd.DataFrame(DF[f"reg_{sufix}"].value_counts()))
    print()

    DF[col_ibge_ref] = pd.to_numeric(DF[col_ibge_ref], errors='coerce')

    return DF



def mes_nome(hoje:datetime.date):
    """
    Função para transformar o número do mês (int) em uma sigla de 3 digitos (ex. 4 - Abr)
    """

    nomes_mes = {
        1: 'Jan',
        2: 'Fev',
        3: 'Mar',
        4: 'Abr',
        5: 'Mai',
        6: 'Jun',
        7: 'Jul',
        8: 'Ago',
        9: 'Set',
        10: 'Out',
        11: 'Nov',
        12: 'Dez'
    }
    mes = hoje.month
    mes_nome = nomes_mes[mes]
    return mes_nome


def mes_nome_completo(hoje:datetime.date):
    """
    Função para transformar o número do mês (int) em uma sigla de 3 digitos (ex. 4 - abril)
    """

    nomes_mes = {
        1: 'janeiro',
        2: 'fevereiro',
        3: 'março',
        4: 'abril',
        5: 'maio',
        6: 'junho',
        7: 'julho',
        8: 'agosto',
        9: 'setembro',
        10: 'outubro',
        11: 'novembro',
        12: 'dezembro'
    }
    mes = hoje.month
    mes_nome = nomes_mes[mes]
    return mes_nome



def falhas(row, tempo_inicioTARV, count_cv, tempo_max_cvs, col_prim_disp):
    for i in range(count_cv-1, 0, -1):
        if pd.notnull(row[f"data_hora_coleta_cv_{i}"]) and (row[f"data_hora_coleta_cv_{i}"] - row[col_prim_disp]).days > tempo_inicioTARV and row[f"CV_cat200_{i}"] == ">=200": # 152 dias do início da TARV para que a segunda CV após 28 dias tenha no mínimo 180 dias da TARV
            
            if i - 1 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{i-1}"]) and (row[f"data_hora_coleta_cv_{i-1}"] - row[f"data_hora_coleta_cv_{i}"]).days >= 28 and (row[f"data_hora_coleta_cv_{i-1}"] - row[f"data_hora_coleta_cv_{i}"]).days <= tempo_max_cvs and row[f"CV_cat500_{i-1}"] == ">=500":
                for r in range(i-2, 0, -1):
                    if pd.notnull(row[f"data_hora_coleta_cv_{r}"]) and (row[f"data_hora_coleta_cv_{r}"] - row[f"data_hora_coleta_cv_{i-1}"]).days >= 180 and row[f"CV_cat200_{r}"] == ">=200":
                        if r - 1 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-1}"]) and (row[f"data_hora_coleta_cv_{r-1}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-1}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-1}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-1}"], row[f"data_hora_coleta_cv_{r-1}"]
                        elif r - 2 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-2}"]) and (row[f"data_hora_coleta_cv_{r-2}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-2}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-2}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-1}"], row[f"data_hora_coleta_cv_{r-2}"]
                        elif r - 3 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-3}"]) and (row[f"data_hora_coleta_cv_{r-3}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-3}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-3}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-1}"], row[f"data_hora_coleta_cv_{r-3}"]
                return row[f"data_hora_coleta_cv_{i-1}"], None
            
            elif i - 2 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{i-2}"]) and (row[f"data_hora_coleta_cv_{i-2}"] - row[f"data_hora_coleta_cv_{i}"]).days >= 28 and (row[f"data_hora_coleta_cv_{i-2}"] - row[f"data_hora_coleta_cv_{i}"]).days <= tempo_max_cvs and row[f"CV_cat500_{i-2}"] == ">=500":
                for r in range(i-3, 0, -1):
                    if pd.notnull(row[f"data_hora_coleta_cv_{r}"]) and (row[f"data_hora_coleta_cv_{r}"] - row[f"data_hora_coleta_cv_{i-2}"]).days >= 180 and row[f"CV_cat200_{r}"] == ">=200":
                        if r - 1 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-1}"]) and (row[f"data_hora_coleta_cv_{r-1}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-1}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-1}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-2}"], row[f"data_hora_coleta_cv_{r-1}"]
                        elif r - 2 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-2}"]) and (row[f"data_hora_coleta_cv_{r-2}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-2}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-2}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-2}"], row[f"data_hora_coleta_cv_{r-2}"]
                        elif r - 3 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-3}"]) and (row[f"data_hora_coleta_cv_{r-3}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-3}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-3}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-2}"], row[f"data_hora_coleta_cv_{r-3}"]
                return row[f"data_hora_coleta_cv_{i-2}"], None
            
            elif i - 3 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{i-3}"]) and (row[f"data_hora_coleta_cv_{i-3}"] - row[f"data_hora_coleta_cv_{i}"]).days >= 28 and (row[f"data_hora_coleta_cv_{i-3}"] - row[f"data_hora_coleta_cv_{i}"]).days <= tempo_max_cvs and row[f"CV_cat500_{i-3}"] == ">=500":
                for r in range(i-4, 0, -1):
                    if pd.notnull(row[f"data_hora_coleta_cv_{r}"]) and (row[f"data_hora_coleta_cv_{r}"] - row[f"data_hora_coleta_cv_{i-3}"]).days >= 180 and row[f"CV_cat200_{r}"] == ">=200":
                        if r - 1 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-1}"]) and (row[f"data_hora_coleta_cv_{r-1}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-1}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-1}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-3}"], row[f"data_hora_coleta_cv_{r-1}"]
                        elif r - 2 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-2}"]) and (row[f"data_hora_coleta_cv_{r-2}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-2}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-2}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-3}"], row[f"data_hora_coleta_cv_{r-2}"]
                        elif r - 3 > 0 and pd.notnull(row[f"data_hora_coleta_cv_{r-3}"]) and (row[f"data_hora_coleta_cv_{r-3}"] - row[f"data_hora_coleta_cv_{r}"]).days >= 28 and (row[f"data_hora_coleta_cv_{r-3}"] - row[f"data_hora_coleta_cv_{r}"]).days <= tempo_max_cvs and row[f"CV_cat500_{r-3}"] == ">=500":
                            return row[f"data_hora_coleta_cv_{i-3}"], row[f"data_hora_coleta_cv_{r-3}"]
                return row[f"data_hora_coleta_cv_{i-3}"], None
            
    return None, None



def taxa_crescimento(DF1:pd.DataFrame, Colunas_analise:list, periodo:str = "Anual", ordem:list = [1,2,3,4,5]):
    """
    Calcula a taxa de crescimento de diversas variáveis em um DataFrame ao longo do tempo, ajustando um modelo de Regressão Linear Generalizada com Ajuste de Autocorrelação (GLSAR).
    O DataFrame passado, deve estar no formato onde cada coluna é uma análise independente, e cada linha é um ponto de coleta.

    Parameters
    ----------
    DF1 : pd.DataFrame
        O DataFrame contendo as colunas de variáveis a serem analisadas.
        
    Colunas_analise : list
        Lista de strings representando os nomes das colunas de variáveis que serão analisadas para calcular a taxa de crescimento.
        
    periodo : str, opcional
        O período de análise para o cálculo da taxa de crescimento. O padrão é 'Anual'.

    Returns
    -------
    pd.DataFrame
        Um DataFrame contendo os resultados da análise, incluindo coeficiente de regressão, intervalos de confiança, valor-p, R² ajustado, estatística de Durbin-Watson, parâmetro Rho e a taxa de crescimento calculada para cada variável.
    """

    if periodo == "Anual":
        DF1 = DF1.drop(DF1.index[-1])
    
    for i in DF1.columns:
        DF1[f"ln_{i}"] = DF1[i].apply(lambda x: math.log(float(np.where(x != 0, x, 1))))
        
    DF1["Sequencia"] = range(1, len(DF1) + 1)
        
    Taxa_Cresc = pd.DataFrame(columns=["Ordem", "Coluna", "Coeficiente", "IC95_Min", "IC95_max", "P>|t|", "Rquad", 
                                        f"Taxa_{periodo}", "Taxa_ICmin", "Taxa_ICmax", "Durbin_Watson", "Rho", "Shapiro_resid_p"])

    Taxa_Cresc = Taxa_Cresc.astype("Float64")
    modelos = {}
    for i in Colunas_analise:
        X = sm.add_constant(DF1["Sequencia"])
        y = DF1[f"ln_{i}"]


        ar_model = sm.OLS(y, X).fit()
        for order in ordem:
            rho, _ = yule_walker(ar_model.resid, order=order)
            Reg = sm.GLSAR(y, X, rho=rho).fit()
            stats, p = shapiro(Reg.resid)
            if p > 0.05:
                break
        
        if p < 0.05:
            rho, _ = yule_walker(ar_model.resid, order=1)
            Reg = sm.GLSAR(y, X, rho=rho).fit()
            stats, p = shapiro(Reg.resid)
            order = 1

        modelos[i] = Reg

        tbl = Reg.summary().tables[1]
    
        coef = float(tbl.data[2][1])
        ICmin = float(tbl.data[2][5])
        ICmax = float(tbl.data[2][6])
        p_val = float(tbl.data[2][4])
        Rquad = float(Reg.summary().tables[0].data[0][-1])
        Durbin_Watson = float(Reg.summary().tables[2].data[0][-1])
        
        Taxa = round((math.exp(coef) -1)*100,4)
        Taxa_min = round((math.exp(ICmin) -1)*100,4)
        Taxa_max = round((math.exp(ICmax) -1)*100,4)
        
        Nova_linha = pd.DataFrame([{
            "Coluna": i,
            "Coeficiente": coef,
            "IC95_Min": ICmin,
            "IC95_max": ICmax,
            "P>|t|": p_val,
            "Rquad": Rquad,
            "Ordem": order,
            f"Taxa_{periodo}": Taxa,
            "Taxa_ICmin": Taxa_min,
            "Taxa_ICmax": Taxa_max,
            "Durbin_Watson": Durbin_Watson,
            "Rho": rho if order == 1 else rho.tolist(),
            "Shapiro_resid_p": p
        }])
        Taxa_Cresc = pd.concat([Taxa_Cresc, Nova_linha], ignore_index=True)
    
    Taxa_Cresc.set_index("Coluna", inplace = True)
    
    return Taxa_Cresc, modelos



def relatorio_taxa(DF:pd.DataFrame, periodo:str = "Anual"):
    print()
    print(f"Taxa de crescimento {periodo} calculada pelo modelo generalizado dos quadrados ajustados:")
    print("------------------------------------------------------------------------------")

    for index, row in DF.iterrows():
        print(f"\nColuna de Análise: {index}")
        print(f"Coeficiente: {row['Coeficiente']:.4f}")
        print(f"IC 95%: ({row['IC95_Min']:.4f}, {row['IC95_max']:.4f})")
        print(f"P>|t|: {row['P>|t|']:.4f}")
        print(f"R²: {row['Rquad']:.4f}")
        print(f"Durbin-Watson: {row['Durbin_Watson']:.4f}")
        print(f"Rho: {row['Rho']}")
        print(f"Taxa {periodo} de Crescimento: {row[f'Taxa_{periodo}']:.2f}%")
        print(f"Intervalo de Confiança da Taxa Anual: ({row['Taxa_ICmin']:.2f}%, {row['Taxa_ICmax']:.2f}%)")
        if row['Shapiro_resid_p'] > 0.05:
            print(f"A distribuição dos resíduos do modelo adere à normalidade")
        else:
            print(f"A distribuição dos resíduos do modelo NÃO adere à normalidade")
        print("------------------------------------------------------------------------------")



def relatorio_MannKendall(DF:pd.DataFrame):
    print("\nTeste de Mann-Kendall para Avaliar a Tendência da Reta:")
    print("===================================================================")

    for grupo in DF.index:
        dados = DF.loc[grupo]
        mk_result = mk.original_test(dados.values)
        
        print(f"Grupo: {grupo}")
        print(f"  - Tendência: {mk_result.trend}")
        print(f"  - p-value: {mk_result.p:.3f}")
        print(f"  - Tau: {mk_result.Tau:.3f}")
        print(f"  - Inclinação: {mk_result.slope:.3f}")
        print("---------------------------------------------------------------")



def Teste_variação_zero(DF:pd.DataFrame):
    print("Teste T ou Wilcoxon para Avaliar se a Média (T) ou Mediana (Wilcoxon) das Variações Anuais Tendem a Zero")
    print("==============================================================================================")

    for grupo in DF.index:
        dados = DF.loc[grupo]
        
        # Teste de normalidade de Shapiro-Wilk
        stats, p = shapiro(dados.values)
        
        # Se a amostra segue distribuição normal, usa o teste T; caso contrário, usa o teste de Wilcoxon
        if p > 0.05:
            t_statistic, p_value = ttest_1samp(dados.values, 0)
            print(f"Grupo: {grupo}")
            print(f"  - Teste: Teste T")
            print(f"  - Estatística T: {t_statistic:.3f}")
            print(f"  - P-value: {p_value:.3f}")
            print()
        else:
            wilcoxon_statistic, p_value = wilcoxon(dados.values)
            print(f"Grupo: {grupo}")
            print(f"  - Teste: Teste de Wilcoxon")
            print(f"  - Estatística de Wilcoxon: {wilcoxon_statistic:.3f}")
            print(f"  - P-value: {p_value:.3f}")
            print("----------------------------------------------------------------------------------------------")



def obter_cor(var, valor,cores:dict):
    if var in cores and valor in cores[var]:
        return cores[var][valor]
    return None  # Cor aleatória se não encontrado



def grafico_perc_empilhado(DF: pd.DataFrame, index: str, variaveis: list, cores: dict, numero_fig: int = 1, titulo: str = None,
                           ylabel: str = None, MannKendall: bool = True, color_text: str = "black", fontsize_text: int = 9,
                           unica_figura: bool = False, casa_decimal:int = 0, rotacao_x:int = 45, legenda:str = None, crosstab:bool = True,
                           drop_sem_info = False):
    
    # Determinar o número de gráficos para ajustar o layout se necessário
    n_vars = len(variaveis)
    
    # Preparação para uma única figura com múltiplos subplots, se necessário
    if unica_figura:
        n_rows = (n_vars + 1) // 2  # Número de linhas necessárias
        fig, axs = plt.subplots(n_rows, 2, figsize=(12, 6 * n_rows))
        axs = axs.flatten()  # Achatar o array de eixos para fácil iteração
    else:
        fig = None  # Não necessário para múltiplas figuras separadas
    
    for i, var in enumerate(variaveis):
        if crosstab:
            DF1 = pd.crosstab(index=DF[index], columns=DF[var], normalize="index") * 100
        else:
            DF1 = DF.copy()
        
        if drop_sem_info in DF1.columns:
            DF1 = DF1.drop(columns=[drop_sem_info])

        # Ordena as colunas de acordo com a ordem no dicionário de cores, se disponível
        if var in cores:
            ordem = [col for col in cores[var].keys() if col in DF1.columns]
            DF1 = DF1[ordem]
                    
        if index in cores:
            ordem_idx = [idx for idx in cores[index].keys() if idx in DF1.index]
            DF1 = DF1.reindex(ordem_idx)
        
        if unica_figura:
            ax = axs[i]
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
        
        bottom = None
        for colunas in DF1.columns:
            cor = obter_cor(var, colunas, cores)
            if bottom is not None:
                ax.bar(DF1.index, DF1[colunas], label=colunas, color=cor, bottom=bottom)
            else:
                ax.bar(DF1.index, DF1[colunas], label=colunas, color=cor)
            
            for j, ano in enumerate(DF1.index):
                if bottom is not None:
                    ax.text(ano, bottom[j] + DF1[colunas].iloc[j] / 2, f'{DF1[colunas].iloc[j]:.{casa_decimal}f}%', ha='center', va='center', fontsize=fontsize_text, color=color_text, weight='bold')
                else:
                    ax.text(ano, DF1[colunas].iloc[j] / 2, f'{DF1[colunas].iloc[j]:.{casa_decimal}f}%', ha='center', va='center', fontsize=fontsize_text, color=color_text, weight='bold')
            
            if bottom is None:
                bottom = np.array(DF1[colunas])
            else:
                bottom += np.array(DF1[colunas])
        
        ax.set_title(titulo)
        ax.set_ylabel(ylabel if ylabel else 'Percentual (%)')
        ax.set_ylim(0, 100)
        ax.set_xticks(DF1.index)
        ax.set_xticklabels(DF1.index, rotation=rotacao_x)
        ax.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        if legenda == "lateral":
            ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', fancybox=True, ncol=DF1.shape[1], reverse=True)
        else:
            ax.legend(bbox_to_anchor=(1, 0.8), fancybox=True, reverse=True)

        if not unica_figura:
            plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")
            plt.show()
            
        if MannKendall:
            print()
            print()
            relatorio_MannKendall(DF=DF1.T)
    
    if unica_figura:
        plt.tight_layout()
        plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")
        plt.show()



def grafico_perc_empilhado_transposto(DF: pd.DataFrame, index: list, variaveis: str, cores: dict, numero_fig: int = 1, titulo: str = None,
                                      ylabel: str = None, MannKendall: bool = True, color_text: str = "black", fontsize_text: int = 9,
                                      unica_figura: bool = False, casa_decimal:int = 0, rotacao_x:int = 45, drop_sem_info = False):
    
    # Determinar o número de gráficos para ajustar o layout se necessário
    n_vars = len(index)
    
    # Preparação para uma única figura com múltiplos subplots, se necessário
    if unica_figura:
        n_rows = (n_vars + 1) // 2  # Número de linhas necessárias
        fig, axs = plt.subplots(n_rows, 2, figsize=(12, 6 * n_rows))
        axs = axs.flatten()  # Achatar o array de eixos para fácil iteração
    else:
        fig = None  # Não necessário para múltiplas figuras separadas
    
    for i, ind in enumerate(index):
        DF1 = pd.crosstab(index=DF[ind], columns=DF[variaveis], normalize="index") * 100

        if drop_sem_info in DF1.index:
            DF1 = DF1.drop([drop_sem_info])

        # Ordena as colunas de acordo com a ordem no dicionário de cores, se disponível
        if variaveis in cores:
            ordem = [col for col in cores[variaveis].keys() if col in DF1.columns]
            DF1 = DF1[ordem]
                    
        if ind in cores:
            ordem_idx = [idx for idx in cores[ind].keys() if idx in DF1.index]
            DF1 = DF1.reindex(ordem_idx)
        
        if unica_figura:
            ax = axs[i]
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
        
        bottom = None
        for colunas in DF1.columns:
            cor = obter_cor(variaveis, colunas, cores)
            if bottom is not None:
                ax.bar(DF1.index, DF1[colunas], label=colunas, color=cor, bottom=bottom)
            else:
                ax.bar(DF1.index, DF1[colunas], label=colunas, color=cor)
            
            for j, ano in enumerate(DF1.index):
                if bottom is not None:
                    ax.text(ano, bottom[j] + DF1[colunas].iloc[j] / 2, f'{DF1[colunas].iloc[j]:.{casa_decimal}f}%', ha='center', va='center', fontsize=fontsize_text, color=color_text, weight='bold')
                else:
                    ax.text(ano, DF1[colunas].iloc[j] / 2, f'{DF1[colunas].iloc[j]:.{casa_decimal}f}%', ha='center', va='center', fontsize=fontsize_text, color=color_text, weight='bold')
            
            if bottom is None:
                bottom = np.array(DF1[colunas])
            else:
                bottom += np.array(DF1[colunas])
        
        ax.set_title(titulo)
        ax.set_ylabel(ylabel if ylabel else 'Percentual (%)')
        ax.set_ylim(0, 100)
        ax.set_xticks(DF1.index)
        ax.set_xticklabels(DF1.index, rotation=rotacao_x)
        ax.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        if not unica_figura:
            ax.legend(bbox_to_anchor=(1, 0.8), fancybox=True, reverse=True)
            plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")
            numero_fig += 1
            plt.show()
            
        if MannKendall:
            print()
            print()
            relatorio_MannKendall(DF=DF1.T)
    
    if unica_figura:
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc='lower center', fancybox=True, ncol=len(labels), reverse=True, bbox_to_anchor=(0.5, -0.05), frameon=False)
        plt.tight_layout()
        plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")
        plt.show()



def grafico_linha_tend(DF: pd.DataFrame, var_estrat: str, cores: dict, numero_fig: int = 1, titulo: str = None,
                        ylabel: str = None):

    plt.figure(figsize=(12, 6))


    print("Resultados da Regressão Linear:")
    print("==========================================")

    if var_estrat in cores:
        ordem = [idx for idx in cores[var_estrat].keys() if idx in DF.index]
        DF = DF.reindex(ordem)

    for grupo in DF.index:
        dados = DF.loc[grupo]
        cor = obter_cor(var_estrat, dados.name, cores)
        plt.plot(dados.index, dados.values, label=grupo, color = cor)
        
        # Ajuste do modelo de regressão linear
        x = np.arange(len(dados)).reshape(-1, 1)
        y = dados.values.reshape(-1, 1)
        modelo = LinearRegression().fit(x, y)
        y_pred = modelo.predict(x)
        # Adicionando a linha de tendência aos últimos 18 meses
        plt.plot(dados.index, y_pred.flatten(), linestyle='--', label=f'_Tendência', color = cor)
        
        # Coeficiente angular (inclinação) e R²
        inclinacao = modelo.coef_[0][0]
        r2 = r2_score(y, y_pred)
        
        print(f"Grupo: {grupo}")
        print(f"  - Inclinação (\u03B1): {inclinacao:.3f}")
        print(f"  - Coeficiente de Determinação (R²): {r2:.2f}")
        print("------------------------------------------")
    
    print()

    # Defina um título para o gráfico
    plt.title(titulo)
    plt.ylabel(ylabel)


    # Adicione um grid de fundo
    plt.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")

    # Remova a moldura do gráfico
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Configure o eixo x para mostrar os números dos anos
    plt.xticks(dados.index)

    # Gire os rótulos do eixo x para facilitar a leitura
    plt.xticks(rotation=45)

    plt.ylim(bottom=0)

    # Adicione a legenda
    plt.legend(loc='upper left', bbox_to_anchor=(1, 0.2), fancybox=True)

    # Salva a figura
    plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")

    # Exiba o gráfico
    plt.show()



def grafico_variacao_anual(DF: pd.DataFrame, meses:int, var_estrat: str, cores: dict, numero_fig: int = 1, titulo: str = None,
                            ylabel: str = None, MannKendall: bool = True, Teste_variacao:bool = True):
    
    Variação_anual = ((DF / DF.shift(12, axis = 1) - 1) * 100).iloc[:, -meses:]
    plt.figure(figsize=(12, 6))

    if var_estrat in cores:
        ordem = ordem = [idx for idx in cores[var_estrat].keys() if idx in DF.index]
        Variação_anual = Variação_anual.reindex(ordem)

    for grupo in Variação_anual.index:
        dados = Variação_anual.loc[grupo]
        cor = obter_cor(var_estrat,dados.name, cores)
        plt.plot(dados.index, dados.values, label=grupo, color = cor)

        
    # Adicione um grid de fundo
    plt.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")

    # Configure o eixo x para mostrar os números dos anos
    plt.xticks(dados.index)
    # Gire os rótulos do eixo x para facilitar a leitura
    plt.xticks(rotation=45)

    # Defina um título para o gráfico
    plt.title(titulo)
    plt.ylabel(ylabel)

    # Remova a moldura do gráfico
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)

    plt.legend(bbox_to_anchor=(1, 0.8), fancybox=True)

    # Salva a figura
    plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")

    plt.show()
    if MannKendall:
        print()
        print()
        relatorio_MannKendall(DF=Variação_anual)
    
    if Teste_variacao:
        print()
        print()
        Teste_variação_zero(DF=Variação_anual)



def grafico_barras_sobrepostas(DF:pd.DataFrame, variaveis:list, cores: dict, grupo_cor = "Populacao",
                               normalizacao:int = 1, numero_fig: int = 1, titulo: str = None,
                               ylabel: str = None, color_text: str = "white", fontsize_text: int = 12,
                               MannKendall:bool = True, posicao_text:int = 0.1):

    plt.figure(figsize=(12, 6))

    for var in variaveis:
        cor = obter_cor(grupo_cor, var, cores)
        # Crie um gráfico de barras verticais com a série de anos e o número de pessoas
        plt.bar(DF.index, DF[var]/normalizacao, color=cor, label=var)

    # Defina um título para o gráfico
    plt.title(titulo)
    plt.ylabel(ylabel)

    # Ajuste o intervalo do eixo y
    plt.ylim(0, (DF[variaveis]/normalizacao).max().max() + 5)

    # Adicione um grid de fundo
    plt.grid(True, linestyle='--', axis="y", linewidth=0.1, color="black")

    # Remova a moldura do gráfico
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Configure o eixo x para mostrar os números dos anos
    ax.set_xticks(DF.index)

    for var in variaveis:
    # Adicione os valores dentro das barras  
        for index, value in zip(DF.index, DF[var]/normalizacao):
            plt.text(index, value + posicao_text, f'{value:.0f}', fontsize=fontsize_text, color=color_text, ha='center', va='bottom')

    # Adicione a legenda
    plt.legend(bbox_to_anchor=(1, 0.2), fancybox=True)

    # Salva a figura
    plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")

    # Exiba o gráfico
    plt.show()   

    if MannKendall:
        print()
        print()
        relatorio_MannKendall(DF=DF[variaveis].T)



def marcar_ultimas_antes(DF:pd.DataFrame, data_ref:str, data_busca:str, n_busca:int, lista_cols:list = None,
                        n_salvos:int = 2, nomes_seq:list = ["ult", "penult"], fillna = pd.NaT):

    """
    Marca as últimas ocorrências de colunas específicas em um DataFrame antes de uma data de referência.

    A função itera sobre cada linha de um DataFrame e busca as últimas datas em uma série de colunas que ocorrem 
    antes de uma data de referência. As informações correspondentes às colunas relacionadas são copiadas para 
    novas colunas com sufixos indicando a ordem das ocorrências encontradas.

    Parameters
    ----------
    DF : pd.DataFrame
        O DataFrame contendo as colunas a serem analisadas.
        
    data_ref : str
        Nome da coluna que contém as datas de referência para a busca.
        
    data_busca : str
        Nome da coluna base onde serão buscadas as datas anteriores à data de referência.
        
    n_busca : int
        Número máximo de colunas sequenciais a serem analisadas (e.g., data_busca_0, data_busca_1, ...).
        
    lista_cols : list, opcional
        Lista de colunas adicionais cujos valores serão copiados se as datas correspondentes forem encontradas. 
        As colunas devem estar associadas com a série de datas buscadas.
        
    n_salvos : int, opcional
        Número de ocorrências a serem salvas para cada coluna (padrão é 2, salvando a última e a penúltima).
        
    nomes_seq : list, opcional
        Lista de sufixos a serem usados para nomear as colunas geradas (padrão é ["ult", "penult"]).
        
    fillna : valor, opcional
        Valor a ser preenchido caso nenhuma ocorrência seja encontrada. Padrão é pd.NaT para valores de data.

    Returns
    -------
    None
        A função modifica o DataFrame original adicionando novas colunas com as últimas ocorrências encontradas.

    Notes
    -----
    - A função assume que as colunas de data e as colunas adicionais possuem uma sequência numerada (e.g., "data_busca_0", "data_busca_1").
    - Se nenhuma data anterior for encontrada, as novas colunas são preenchidas com o valor de `fillna`.
    """

    for index, row in DF.iterrows():
        found = False
        for i in range(n_busca):
            if (row[data_ref] - row[f"{data_busca}_{i}"]).days > 0:
                for col in [data_busca] + lista_cols:
                    for n,nome in zip(range(n_salvos),nomes_seq):
                        DF.at[index, f"{col}_{nome}"] = row[f"{col}_{i+n}"]
                
                found = True
                break  # Interrompe o loop após a primeira ocorrência
        
        if not found:
            # Se nenhum teste foi bem-sucedido, você pode definir valores padrão ou deixar em branco
            for col in [data_busca] + lista_cols:
                for n,nome in zip(range(n_salvos),nomes_seq):
                    DF.at[index, f"{col}_{nome}"] = fillna

    return DF



def ANACOR_Multipla(DF:pd.DataFrame, var_ref:str, variaveis:list,
                    dimensoes:int = 2, numero_fig: int = 1,
                    graf_obs:bool = False, D3:bool = True):
    
    DF = DF[variaveis + [var_ref]].copy()   
    for var in variaveis:
        tabela_mca = pd.crosstab(DF[var_ref], DF[var])
        display(tabela_mca)
    
        # Analisando a significância estatística das associações (teste qui²)    
        tab = chi2_contingency(tabela_mca)    
        print(f"{var_ref} x {var}")
        print(f"estatística qui²: {round(tab[0], 2)}")
        print(f"p-valor da estatística: {round(tab[1], 4)}")
        print(f"graus de liberdade: {tab[2]}")
        print()


    mca = prince.MCA(n_components=dimensoes).fit(DF)  
    
    # Quantidade total de categorias
    mca.J_ 
    # Quantidade de variáveis na análise
    mca.K_  
    # Quantidade de dimensões
    quant_dim = mca.J_ - mca.K_  
    # Resumo das informações
    print()
    print(f"quantidade total de categorias: {mca.J_}")
    print(f"quantidade de variáveis: {mca.K_}")
    print(f"quantidade de dimensões: {quant_dim}")
    print()
    
    # Obtendo os eigenvalues  
    tabela_autovalores = mca.eigenvalues_summary
    print("Tabela de Autovalores")
    print(tabela_autovalores)
    print("Inécia Total: ", mca.total_inertia_)
    print("Média da Inércia: ", mca.total_inertia_/quant_dim)    
    print()

    # Obtendo as coordenadas principais das categorias das variáveis
    coord_padrao = mca.column_coordinates(DF)/np.sqrt(mca.eigenvalues_) # Coordenadas padrão
    coord_obs = mca.row_coordinates(DF) # Coordenadas das observações

    if dimensoes == 2:
        # Plotando o mapa perceptual (coordenadas-padrão) para 2 dimensões   
        
        # Primeiro passo: gerar um DataFrame detalhado      
        chart = coord_padrao.reset_index()
        
        nome_categ=[]
        for col in DF:
            nome_categ.append(DF[col].sort_values(ascending=True).unique())
            categorias = pd.DataFrame(nome_categ).stack().reset_index()
        
        var_chart = pd.Series(chart['index'].str.split('_', expand=True).iloc[:,0])
        
        chart_df_mca = pd.DataFrame({'categoria': chart['index'],
                                     'obs_x': chart[0],
                                     'obs_y': chart[1],
                                     'variavel': var_chart,
                                     'categoria_id': categorias[0]})
        
        # Segundo passo: gerar o gráfico de pontos            
        def label_point(x, y, val, ax):
            a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
            for i, point in a.iterrows():
                ax.text(point['x'] + 0.03, point['y'] - 0.02, point['val'], fontsize=5)
        
        label_point(x = chart_df_mca['obs_x'],
                    y = chart_df_mca['obs_y'],
                    val = chart_df_mca['categoria_id'],
                    ax = plt.gca())
        
        sns.scatterplot(data=chart_df_mca, x='obs_x', y='obs_y', hue='variavel', s=30)
        sns.despine(top=True, right=True, left=False, bottom=False)
        plt.axhline(y=0, color='lightgrey', ls='--', linewidth=0.8)
        plt.axvline(x=0, color='lightgrey', ls='--', linewidth=0.8)
        plt.tick_params(size=2, labelsize=6)
        plt.legend(bbox_to_anchor=(1.25,-0.2), fancybox=True, shadow=True, ncols=10, fontsize='5')
        plt.title("Mapa Perceptual - MCA", fontsize=12)
        plt.xlabel(f"Dim. 1: {tabela_autovalores.iloc[0,1]} da inércia", fontsize=8)
        plt.ylabel(f"Dim. 2: {tabela_autovalores.iloc[1,1]} da inércia", fontsize=8)
        plt.savefig(f"Figura_{numero_fig}.png", dpi=600, bbox_inches="tight")
        plt.show()

        if graf_obs:
            # Gráfico das observações       
            coord_obs[var_ref] = DF[var_ref]  
            sns.scatterplot(data=coord_obs, x=0, y=1, hue=var_ref, s=20)
            plt.title("Mapa das Observações - MCA", fontsize=12)
            plt.xlabel("Dimensão 1", fontsize=8)
            plt.ylabel("Dimensão 2", fontsize=8)
            plt.show()

    if dimensoes == 3:
        if D3:
            # Plotando o mapa perceptual (coordenadas-padrão) para 3 dimensões
            
            # Primeiro passo: gerar um DataFrame detalhado
            chart = coord_padrao.reset_index()
            
            var_chart = pd.Series(chart['index'].str.split('_', expand=True).iloc[:,0])
            
            nome_categ=[]
            for col in DF:
                nome_categ.append(DF[col].sort_values(ascending=True).unique())
                categorias = pd.DataFrame(nome_categ).stack().reset_index()
            
            chart_df_mca = pd.DataFrame({'categoria': chart['index'],
                                        'obs_x': chart[0],
                                        'obs_y': chart[1],
                                        'obs_z': chart[2],
                                        'variavel': var_chart,
                                        'categoria_id': categorias[0]})
            
            # Segundo passo: gerar o gráfico de pontos      
            fig = px.scatter_3d(chart_df_mca, 
                                x='obs_x', 
                                y='obs_y', 
                                z='obs_z',
                                color='variavel',
                                text=chart_df_mca.categoria_id)
            fig.show()    
        
        else:

            # Plotando o mapa perceptual (coordenadas-padrão) para 2 dimensões   
        
            # Primeiro passo: gerar um DataFrame detalhado      
            chart = coord_padrao.reset_index()
            
            nome_categ=[]
            for col in DF:
                nome_categ.append(DF[col].sort_values(ascending=True).unique())
                categorias = pd.DataFrame(nome_categ).stack().reset_index()
            
            var_chart = pd.Series(chart['index'].str.split('_', expand=True).iloc[:,0])
            
            chart_df_mca = pd.DataFrame({'categoria': chart['index'],
                                        'obs_x': chart[0],
                                        'obs_y': chart[1],
                                        'variavel': var_chart,
                                        'categoria_id': categorias[0]})
            
            # Segundo passo: gerar o gráfico de pontos            
            def label_point(x, y, val, ax):
                a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
                for i, point in a.iterrows():
                    ax.text(point['x'] + 0.03, point['y'] - 0.02, point['val'], fontsize=5)
            
            label_point(x = chart_df_mca['obs_x'],
                        y = chart_df_mca['obs_y'],
                        val = chart_df_mca['categoria_id'],
                        ax = plt.gca())
            
            sns.scatterplot(data=chart_df_mca, x='obs_x', y='obs_y', hue='variavel', s=30)
            sns.despine(top=True, right=True, left=False, bottom=False)
            plt.axhline(y=0, color='lightgrey', ls='--', linewidth=0.8)
            plt.axvline(x=0, color='lightgrey', ls='--', linewidth=0.8)
            plt.tick_params(size=2, labelsize=6)
            plt.legend(bbox_to_anchor=(1.25,-0.2), fancybox=True, shadow=True, ncols=10, fontsize='5')
            plt.title("Mapa Perceptual - MCA dimensões x e y", fontsize=12)
            plt.xlabel(f"Dim. 1: {tabela_autovalores.iloc[0,1]} da inércia", fontsize=8)
            plt.ylabel(f"Dim. 2: {tabela_autovalores.iloc[1,1]} da inércia", fontsize=8)
            plt.savefig(f"Figura_{numero_fig}a.png", dpi=600, bbox_inches="tight")
            plt.show()

            # Plotando a outra dimensão
            chart_df_mca2 = pd.DataFrame({'categoria': chart['index'],
                                        'obs_x': chart[0],
                                        'obs_y': chart[2],
                                        'variavel': var_chart,
                                        'categoria_id': categorias[0]})
            
            # Segundo passo: gerar o gráfico de pontos            
            def label_point(x, y, val, ax):
                a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
                for i, point in a.iterrows():
                    ax.text(point['x'] + 0.03, point['y'] - 0.02, point['val'], fontsize=5)
            
            label_point(x = chart_df_mca2['obs_x'],
                        y = chart_df_mca2['obs_y'],
                        val = chart_df_mca2['categoria_id'],
                        ax = plt.gca())
            
            sns.scatterplot(data=chart_df_mca2, x='obs_x', y='obs_y', hue='variavel', s=30)
            sns.despine(top=True, right=True, left=False, bottom=False)
            plt.axhline(y=0, color='lightgrey', ls='--', linewidth=0.8)
            plt.axvline(x=0, color='lightgrey', ls='--', linewidth=0.8)
            plt.tick_params(size=2, labelsize=6)
            plt.legend(bbox_to_anchor=(1.25,-0.2), fancybox=True, shadow=True, ncols=10, fontsize='5')
            plt.title("Mapa Perceptual - MCA dimensões x e z", fontsize=12)
            plt.xlabel(f"Dim. 1: {tabela_autovalores.iloc[0,1]} da inércia", fontsize=8)
            plt.ylabel(f"Dim. 3: {tabela_autovalores.iloc[2,1]} da inércia", fontsize=8)
            plt.savefig(f"Figura_{numero_fig}b.png", dpi=600, bbox_inches="tight")
            plt.show()

            # Plotando as dimensões 2 e 3
            chart_df_mca2 = pd.DataFrame({'categoria': chart['index'],
                                        'obs_x': chart[1],
                                        'obs_y': chart[2],
                                        'variavel': var_chart,
                                        'categoria_id': categorias[0]})
            
            # Segundo passo: gerar o gráfico de pontos            
            def label_point(x, y, val, ax):
                a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
                for i, point in a.iterrows():
                    ax.text(point['x'] + 0.03, point['y'] - 0.02, point['val'], fontsize=5)
            
            label_point(x = chart_df_mca2['obs_x'],
                        y = chart_df_mca2['obs_y'],
                        val = chart_df_mca2['categoria_id'],
                        ax = plt.gca())
            
            sns.scatterplot(data=chart_df_mca2, x='obs_x', y='obs_y', hue='variavel', s=30)
            sns.despine(top=True, right=True, left=False, bottom=False)
            plt.axhline(y=0, color='lightgrey', ls='--', linewidth=0.8)
            plt.axvline(x=0, color='lightgrey', ls='--', linewidth=0.8)
            plt.tick_params(size=2, labelsize=6)
            plt.legend(bbox_to_anchor=(1.25,-0.2), fancybox=True, shadow=True, ncols=10, fontsize='5')
            plt.title("Mapa Perceptual - MCA dimensões y e z", fontsize=12)
            plt.xlabel(f"Dim. 2: {tabela_autovalores.iloc[1,1]} da inércia", fontsize=8)
            plt.ylabel(f"Dim. 3: {tabela_autovalores.iloc[2,1]} da inércia", fontsize=8)
            plt.savefig(f"Figura_{numero_fig}c.png", dpi=600, bbox_inches="tight")
            plt.show()



def calcular_ic_diff_percent_bootstrap(data1, data2, n_iterations=10000, alpha=0.05, tipo = "media"):
    """
    Calcula o intervalo de confiança bootstrap para a diferença percentual da razão entre as medianas
    de duas amostras.
    """
    # Armazena as diferenças percentuais da razão nas iterações de bootstrap
    bootstrap_diffs_percent = []
    
    for _ in range(n_iterations):
        # Reamostra com reposição
        sample1 = resample(data1)
        sample2 = resample(data2)

        if tipo == "media":

            # Calcular a razão das médias
            mean1 = np.mean(sample1)
            mean2 = np.mean(sample2)
            ratio = mean2 / mean1
        
        elif tipo == "mediana":
        
            # Calcule a razão das medianas
            median1 = np.median(sample1)
            median2 = np.median(sample2)
            ratio = median2 / median1
            
     
        # Calcular a diferença percentual da razão
        diff_percent = (ratio - 1) * 100
        bootstrap_diffs_percent.append(diff_percent)
    
    # Calcular o intervalo de confiança para a diferença percentual usando percentis
    ci_percentile = (1 - alpha) * 100
    
    # Intervalo de confiança para a diferença percentual
    lower = np.percentile(bootstrap_diffs_percent, (100 - ci_percentile) / 2)
    upper = np.percentile(bootstrap_diffs_percent, 100 - (100 - ci_percentile) / 2)
    
    return lower, upper



def comparar_medias_testet(df1, df2, identif, alpha=0.05, n_iterations = 10000):
    """
    Compara as médias de duas amostras contidas em dois DataFrames, realizando o teste de Levene,
    o teste t e calculando o intervalo de confiança para a diferença percentual da razão entre as médias.

    Parâmetros:
    - df1, df2: DataFrames contendo as amostras.
    - identif: identificador para o resultado.
    - alpha: nível de significância para os testes (default é 0.05).

    Retorna:
    - dicionário com os resultados do teste e intervalo de confiança.
    """
    
    # Extraindo os dados das colunas dos DataFrames
    data1 = df1.dropna()  # Remover NaN se houver
    data2 = df2.dropna()  # Remover NaN se houver
    
    # Realizando o teste de Levene para homogeneidade de variâncias
    stat_levene, p_levene = levene(data1, data2)
    
    # Decisão sobre igualdade de variâncias
    if p_levene < alpha:
        equal_var = False
        variancias = "significativamente diferentes"
    else:
        equal_var = True
        variancias = "iguais"
    
    # Realizando o teste t para duas amostras independentes
    with suprimir_output():
        stat_t, p_t = ttest_ind(data1, data2, equal_var=equal_var)
    
    # Cálculo do intervalo de confiança para a diferença entre as médias
    mean1 = np.mean(data1)
    mean2 = np.mean(data2)
    ratio = mean2 / mean1
    
    # Calcular a diferença percentual da razão
    diff_percent = round((ratio - 1) * 100, 2)
    
    # Calcular o intervalo de confiança para a diferença percentual da razão utilizando bootstrap
    ci_lower, ci_upper = calcular_ic_diff_percent_bootstrap(data1, data2, n_iterations=n_iterations, alpha=alpha, tipo = "media")
    
    # Preparando os resultados
    resultados = {
        identif: {
            "Teste": f"Teste T com variâncias {variancias}",
            "Estatística do teste": stat_t,
            "Valor-p do teste": p_t,
            "Conclusão do teste": "Os períodos são significativamente diferentes." if p_t < alpha else "Não há diferença significativa entre os períodos.",
            "Diferença Percentual da Razão": round(diff_percent, 2),
            "IC95 Min": round(ci_lower, 2),
            "IC95 Max": round(ci_upper, 2)
        }
    }
    
    return pd.DataFrame(resultados).T



def comparar_medianas_mannwhitney(df1, df2, identif, n_iterations=10000, alpha=0.05):
    """
    Realiza o teste de Mann-Whitney para comparar duas amostras e calcula o intervalo de confiança para a 
    diferença percentual da razão entre as medianas.
    """
    
    # Extraindo os dados das colunas dos DataFrames
    data1 = df1.dropna()  # Remover NaN se houver
    data2 = df2.dropna()  # Remover NaN se houver
    
    # Teste de Mann-Whitney
    with suprimir_output():
        stat, p_value = mannwhitneyu(data1, data2, alternative='two-sided')

    # Calcular a diferença percentual entre as medianas
    median1 = np.median(data1)
    median2 = np.median(data2)
    
    # Razão das medianas
    ratio = median2 / median1
    
    # Diferença percentual da razão
    diff_percent = round((ratio - 1) * 100, 2)
    
    # Calcular o intervalo de confiança para a diferença percentual da razão utilizando bootstrap
    ci_lower, ci_upper = calcular_ic_diff_percent_bootstrap(data1, data2, n_iterations=n_iterations, alpha=alpha,  tipo = "mediana")
    
    # Preparando os resultados
    resultados = {
        identif: {
            "Teste": "Mann-Whitney",
            "Estatística do teste": stat,
            "Valor-p do teste": p_value,
            "Conclusão do teste": "Os períodos são significativamente diferentes." if p_value < alpha else "Não há diferença significativa entre os períodos.",
            "Diferença Percentual da Razão": diff_percent,
            "IC95 Min": round(ci_lower,2),
            "IC95 Max": round(ci_upper,2)
        }
    }
    
    return pd.DataFrame(resultados).T



def comparar_2periodos(df1, df2, identif, alpha=0.05, n_iterations=10000):
    

    with suprimir_output():
        p1 = shapiro_francia(df1)['p-value']
        p2 = shapiro_francia(df2)['p-value']

    if p1 > 0.5 and p2 > 0.05:
        
        resultado = comparar_medias_testet(df1=df1, df2=df2, identif=identif, alpha=alpha, n_iterations=n_iterations)

    else:

        resultado = comparar_medianas_mannwhitney(df1=df1, df2=df2,identif=identif, n_iterations=n_iterations, alpha=alpha)

    
    Condicao = [
        (resultado["Conclusão do teste"] == "Não há diferença significativa entre os períodos."),
        (resultado["Diferença Percentual da Razão"] >= 0),
        (resultado["Diferença Percentual da Razão"] < 0)
    ]

    Escolha = [
        "Estável", "Aumentou", "Reduziu"
    ]

    resultado["Resultado"] = np.select(Condicao,Escolha, default = "Erro")

    return resultado
