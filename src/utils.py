import pandas as pd

def mes_nome(data):
    """
    Retorna a abreviação do mês em português (Jan, Fev, etc.)
    """
    meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    if pd.isnull(data):
        return ""
    return meses.get(data.month, '')
