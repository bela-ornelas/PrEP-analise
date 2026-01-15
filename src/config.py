import os

# Caminhos Base
BASE_PATH_V = r"V:/"

# Caminho para arquivo de versões de colunas
CAMINHO_COLUNAS_DEFAULT = r"//SAP109/Bancos AMA/Arquivos Atuais/Programas Atuais/Python/Versoes_Bancos de dados.xlsx"

# Caminhos para bases compartilhadas (Hardcoded conforme notebook original)
PATH_CADASTRO_HIV = r"V:/2025/Monitoramento e Avaliação/COMPARTILHADO/AMA - Banco de Dados/AMA-VIP/Bancos Compartilhados HIV/Cadastro.csv"
PATH_PVHA = r"V:/2025/Monitoramento e Avaliação/COMPARTILHADO/AMA - Banco de Dados/AMA-VIP/Bancos Compartilhados HIV/PVHA.csv"
PATH_SINAN_ADULTO = r"V:/2025/Monitoramento e Avaliação/COMPARTILHADO/AMA - Banco de Dados/AMA-VIP/Bancos Compartilhados HIV/Sinan_hiv_adulto.csv"
PATH_PVHA_PRIM_ULT = r"//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PVHA_prim_ult.csv"

# Ordem dos meses para plotagem/ordenação
MONTHS_ORDER = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

# Mapeamentos Geográficos
UF_MAP = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
    '28': 'SE', '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
}

REGIAO_MAP = {
    '11': 'Norte', '12': 'Norte', '13': 'Norte', '14': 'Norte', '15': 'Norte', '16': 'Norte', '17': 'Norte',
    '21': 'Nordeste', '22': 'Nordeste', '23': 'Nordeste', '24': 'Nordeste', '25': 'Nordeste', '26': 'Nordeste',
    '27': 'Nordeste', '28': 'Nordeste', '29': 'Nordeste',
    '31': 'Sudeste', '32': 'Sudeste', '33': 'Sudeste', '35': 'Sudeste',
    '41': 'Sul', '42': 'Sul', '43': 'Sul',
    '50': 'Centro-Oeste', '51': 'Centro-Oeste', '52': 'Centro-Oeste', '53': 'Centro-Oeste'
}
