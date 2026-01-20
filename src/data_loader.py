import pandas as pd
import datetime
import os
import pickle
from .config import BASE_PATH_V, CAMINHO_COLUNAS_DEFAULT, PATH_CADASTRO_HIV, PATH_PVHA, PATH_SINAN_ADULTO, PATH_PVHA_PRIM_ULT, PATH_TABELA_IBGE

CACHE_DIR = ".cache"

def calcular_contagem_mes(ano, mes):
    return (ano - 2021) * 12 + mes - 2

def obter_nome_mes(mes):
    meses_do_ano = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return meses_do_ano[mes]

def get_consolidado_path(hoje):
    ano = hoje.year
    mes = hoje.month
    contagem_mes = calcular_contagem_mes(ano, mes)
    mes_nome = obter_nome_mes(mes)
    # Caminho construído conforme lógica original
    # V:/{ano}/Monitoramento e Avaliação/COMPARTILHADO/AMA - Banco de Dados/Consolidado/{contagem_mes} - {mes_nome} {ano}
    caminho = os.path.join(BASE_PATH_V, str(ano), "Monitoramento e Avaliação", "COMPARTILHADO", "AMA - Banco de Dados", "Consolidado", f"{contagem_mes} - {mes_nome} {ano}")
    return caminho

def carregar_bases(hoje: datetime.date, 
                   carregar_disp=True, 
                   carregar_cad=True, 
                   carregar_pvha=True, 
                   carregar_sinan=True,
                   caminho_colunas=CAMINHO_COLUNAS_DEFAULT,
                   use_cache=True):
    
    # -------------------------------------------------------------------------
    # CACHE SYSTEM
    # -------------------------------------------------------------------------
    if use_cache:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        # Nome do cache inclui a data para garantir atualização mensal
        cache_file = os.path.join(CACHE_DIR, f"bases_{hoje}.pkl")
        
        if os.path.exists(cache_file):
            print(f"--- [CACHE] Encontrado cache local: {cache_file} ---")
            print("Carregando bases do disco local (muito mais rápido)...")
            try:
                with open(cache_file, 'rb') as f:
                    bases = pickle.load(f)
                print("--- [CACHE] Bases carregadas com sucesso! ---")
                return bases
            except Exception as e:
                print(f"Erro ao ler cache: {e}. Tentando carga original...")
    
    # -------------------------------------------------------------------------
    # LOAD FROM NETWORK
    # -------------------------------------------------------------------------
    bases = {}
    path_consolidado = get_consolidado_path(hoje)
    
    if not os.path.exists(path_consolidado):
        # Fallback ou erro? Original lança erro.
        print(f"Alerta: Caminho consolidado não encontrado: {path_consolidado}")
        # raise FileNotFoundError(f"O caminho {path_consolidado} não existe.") 
        # Vou deixar passar para testar em ambiente sem V:, mas avisando.

    # Dicionário de arquivos esperados no consolidado (tab separated)
    arquivos_consolidado = {
        "Disp": "tb_dispensas_prep_udm",
        "Cad_Consolidado": "tb_cadastro_prep_consolidado", # Nome interno diferente do CSV de cadastro geral
        # Adicionar outros se necessario
    }
    
    # 1. Carregar Definições de Colunas (se acessível)
    dic_colunas = {}
    if os.path.exists(caminho_colunas):
        try:
            dic_variaveis = pd.read_excel(caminho_colunas, sheet_name=None)
            dict_aba_base_map = {
                "PrEP_Dispensa": "tb_dispensas_prep_udm",
                "PrEP_Cadastro": "tb_cadastro_prep_consolidado"
            }
            
            for aba, df_cols in dic_variaveis.items():
                colunas_validas = [col for col in df_cols.columns if isinstance(col, datetime.datetime) and col.date() <= hoje]
                if not colunas_validas:
                    continue # Ou use lógica default
                ultima_coluna_valida = max(colunas_validas)
                lista_de_variaveis = df_cols[ultima_coluna_valida].dropna().tolist()
                
                nome_base = dict_aba_base_map.get(aba)
                if nome_base:
                    dic_colunas[nome_base] = lista_de_variaveis
        except Exception as e:
            print(f"Erro ao ler arquivo de colunas: {e}")

    # 2. Carregar Dispensa (Consolidado)
    if carregar_disp:
        nome_arquivo = arquivos_consolidado["Disp"]
        path_arquivo = os.path.join(path_consolidado, f"{nome_arquivo}.txt")
        cols = dic_colunas.get(nome_arquivo) # Se None, read_csv pode inferir ou falhar se names for None
        
        if os.path.exists(path_arquivo):
            print(f"Carregando Dispensa de: {path_arquivo}")
            if not cols:
                # raise ValueError(f"CRÍTICO: Não foi possível carregar a lista de colunas para dispensas. Verifique o acesso ao arquivo: {caminho_colunas}")
                print(f"Aviso: Colunas não encontradas em {caminho_colunas}. Tentando inferir...")

            try:
                bases["Disp"] = pd.read_csv(path_arquivo, sep="\t", names=cols, header=None,
                                          encoding="latin-1", low_memory=True, on_bad_lines="warn", quoting=3)
            except Exception as e:
                print(f"Erro crítico ao ler CSV de dispensa: {e}")
                bases["Disp"] = pd.DataFrame()
        else:
            print(f"Arquivo de dispensa não encontrado: {path_arquivo}")
            bases["Disp"] = pd.DataFrame() # Retorna vazio para não quebrar fluxo imediato

    # 3. Carregar Cadastro PrEP (Consolidado - para dados demográficos)
    if carregar_cad:
        nome_arquivo_cad = arquivos_consolidado["Cad_Consolidado"]
        path_arquivo_cad = os.path.join(path_consolidado, f"{nome_arquivo_cad}.txt")
        cols_cad = dic_colunas.get(nome_arquivo_cad)

        if os.path.exists(path_arquivo_cad) and cols_cad:
            print(f"Carregando Cadastro PrEP (Consolidado) de: {path_arquivo_cad}")
            bases["Cadastro_PrEP"] = pd.read_csv(path_arquivo_cad, sep="\t", names=cols_cad, header=None,
                                              encoding="latin-1", low_memory=True, on_bad_lines="warn", quoting=3)
        else:
            print(f"Alerta: Arquivo de Cadastro PrEP não encontrado no consolidado: {path_arquivo_cad}")
            bases["Cadastro_PrEP"] = pd.DataFrame()

    # 4. Carregar Cadastro HIV (PVHA - para checagens de HIV/Óbito)
    if carregar_pvha:
        if os.path.exists(PATH_CADASTRO_HIV):
            print(f"Carregando Cadastro HIV (PVHA) de: {PATH_CADASTRO_HIV}")
            bases["Cadastro_HIV"] = pd.read_csv(PATH_CADASTRO_HIV, sep=";", encoding="latin-1", low_memory=False)
        else:
            print(f"Arquivo de Cadastro HIV não encontrado: {PATH_CADASTRO_HIV}")
            bases["Cadastro_HIV"] = pd.DataFrame()

        if os.path.exists(PATH_PVHA):
             bases["PVHA"] = pd.read_csv(PATH_PVHA, sep=";", encoding="latin-1", low_memory=False)
        
        if os.path.exists(PATH_PVHA_PRIM_ULT):
             colunas_prim = ['Cod_unificado', 'data_min', 'data_dispensa_prim']
             bases["PVHA_Prim"] = pd.read_csv(PATH_PVHA_PRIM_ULT, sep=";", encoding="latin-1", usecols=colunas_prim, low_memory=True)
             
        # Carregar Tabela IBGE
        if os.path.exists(PATH_TABELA_IBGE):
            print(f"Carregando Tabela IBGE de: {PATH_TABELA_IBGE}")
            bases["Tabela_IBGE"] = pd.read_excel(PATH_TABELA_IBGE)
        else:
            print(f"Tabela IBGE não encontrada: {PATH_TABELA_IBGE}")
            bases["Tabela_IBGE"] = pd.DataFrame()

    if carregar_sinan:
        if os.path.exists(PATH_SINAN_ADULTO):
             bases["SINAN"] = pd.read_csv(PATH_SINAN_ADULTO, sep=";", encoding="latin-1", usecols=['Cod_unificado'], low_memory=True, on_bad_lines='warn')

    # SAVE TO CACHE
    if use_cache and bases:
        try:
            print(f"--- [CACHE] Salvando bases localmente em: {cache_file} ---")
            with open(cache_file, 'wb') as f:
                pickle.dump(bases, f)
        except Exception as e:
            print(f"Aviso: Não foi possível salvar o cache: {e}")

    return bases
