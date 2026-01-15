"""
Programa de Organização das Bases da PrEP

Arquivo: organizacao_bases_PrEP.py

Descrição: Um programa Python com as principais funções para organizar e analisar bases de monitoramento clínico da PrEP

Autor: Assessoria de Monitoramento e Avaliação (AMA)
Organização: Departamento de HIV/Aids, Tuberculose, Hepatites Virais e ISTs (DATHI) - Ministério da Saúde

Data de Criação: 11/02/2025
Versão: 1.0.0
Repositório GitHub: [https://github.com/tbenoliel/Monitoramento-Clinico-HIV]
"""

import numpy as np
import pandas as pd
import datetime
from IPython.display import display
import funcoes_gerais as fg
import os
import re


def carregar_bases(hoje: datetime.date, Cad: bool = False, Disp: bool = False, PrimA: bool = False, Ret30: bool = False, Acomp: bool = False,
                   PEP_disp: bool = False, PEP_ure: bool = False, AidsAv: bool = False,
                   Cad_colsuso:list = None, Disp_colsuso:list = None, PrimA_colsuso:list = None, Ret30_colsuso:list = None, Acomp_colsuso:list = None,
                   PEP_disp_colsuso:list = None, PEP_ure_colsuso:list = None, AidsAv_colsuso:list = None,
                   caminho_colunas: str = "//SAP109/Bancos AMA/Arquivos Atuais/Programas Atuais/Python/Versoes_Bancos de dados.xlsx"):

    """
   
    """
    def calcular_contagem_mes(ano, mes):
        return (ano - 2021) * 12 + mes - 2

    def obter_nome_mes(mes):
        meses_do_ano = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        return meses_do_ano[mes]
    
    ano = hoje.year
    mes = hoje.month
    contagem_mes = calcular_contagem_mes(ano, mes)
    mes_nome = obter_nome_mes(mes)
    caminho = f"V:/{ano}/Monitoramento e Avaliação/COMPARTILHADO/AMA - Banco de Dados/Consolidado/{contagem_mes} - {mes_nome} {ano}"
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"O caminho {caminho} não existe.")

    # Organiza as colunas que serão utilizadas em cada DataFrame de acordo com a data passada
    dict_aba_base = {
        "PrEP_Dispensa": "tb_dispensas_prep_udm",
        "PrEP_PrimAtend": "tb_primeiro_atendimento_prep_consolidado",
        "PrEP_Retorno": "tb_retorno_prep_consolidado",
        "PrEP_Acomp": "tb_acompanhamento_clinico_prep_consolidado",
        "PrEP_Cadastro": "tb_cadastro_prep_consolidado",
        "PEP_Dispensa":"tb_pep_consolidado",
        "PEP_URE":"tb_pep_ure_consolidado",
        "AidsAvançada_Dispensa":"tb_doenca_avancada_consolidado"
    }
    Dic_variaveis = pd.read_excel(caminho_colunas, sheet_name=None)
    Dic_colunas = {}
    for aba, df in Dic_variaveis.items():
        colunas_validas = [coluna for coluna in df.columns if coluna <= hoje]
        if not colunas_validas:
            raise ValueError(f"Nenhuma coluna válida encontrada para a aba {aba} até a data {hoje}.")
        ultima_coluna_valida = max(colunas_validas)
        lista_de_variaveis = df[ultima_coluna_valida].dropna()

        # Substitui o nome da aba pela chave correspondente no dicionário
        aba_substituida = dict_aba_base.get(aba, aba)
        Dic_colunas[aba_substituida] = lista_de_variaveis.tolist()

    bases = {}
    Colunas_Uso = {}

    def adicionar_base(nome, base, cols):
        bases[nome] = base
        Colunas_Uso[nome] = cols

    if Cad:
        adicionar_base("Cad","tb_cadastro_prep_consolidado", Cad_colsuso)
    if Disp:
        adicionar_base("Disp","tb_dispensas_prep_udm", Disp_colsuso)
    if PrimA:
        adicionar_base("PrimA","tb_primeiro_atendimento_prep_consolidado", PrimA_colsuso)
    if Ret30:
        adicionar_base("Ret30","tb_retorno_prep_consolidado", Ret30_colsuso)
    if Acomp:
        adicionar_base("Acomp","tb_acompanhamento_clinico_prep_consolidado", Acomp_colsuso)
    if PEP_disp:
        adicionar_base("PEP_disp","tb_pep_consolidado", PEP_disp_colsuso)
    if PEP_ure:
        adicionar_base("PEP_ure","tb_pep_ure_consolidado", PEP_ure_colsuso)
    if AidsAv:
        adicionar_base("AidsAv","tb_doenca_avancada_consolidado", AidsAv_colsuso)

    DFs = {}
    for (base,base), (nome, cols) in zip(bases.items(), Colunas_Uso.items()):
        colunas = Dic_colunas.get(base)
        if not colunas:
            raise ValueError(f"Colunas não encontradas para a base {base}.")
        df = pd.read_csv(f"{caminho}/{base}.txt", sep="\t", names=colunas,
                        usecols=cols, low_memory=True, index_col=False, engine="c", quoting=3,
                        encoding="latin-1", on_bad_lines="warn")
        DFs[nome] = df
    
    if len(DFs) == 1:  # Se houver apenas um DataFrame, retorne-o diretamente
        return next(iter(DFs.values()))

    else:
        return DFs.values()





    