import pandas as pd
import os
import shutil

def export_to_excel(output_dir, data_fechamento, metrics_dict):
    """
    Gera o arquivo Excel de monitoramento baseado no modelo.
    metrics_dict deve conter os DataFrames calculados.
    """
    data_dt = pd.to_datetime(data_fechamento)
    mes = data_dt.month
    ano = data_dt.year
    
    filename = f"Monitoramento_PrEP_{mes:02d}_{ano}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    # Tentar copiar do modelo se existir localmente
    modelo_path = "Modelo_PrEP.xlsx"
    if os.path.exists(modelo_path):
        print(f"Copiando modelo {modelo_path}...")
        shutil.copyfile(modelo_path, filepath)
        mode = 'a'
        if_sheet_exists = 'overlay'
    else:
        print("Modelo não encontrado localmente. Criando novo arquivo Excel.")
        mode = 'w'
        if_sheet_exists = None

    print(f"Gerando Excel em: {filepath}")
    
    with pd.ExcelWriter(filepath, engine='openpyxl', mode=mode, if_sheet_exists=if_sheet_exists) as writer:
        # 1. Aba Geral
        if 'classificacoes' in metrics_dict:
            # Converter dict para DF para exportar
            c = metrics_dict['classificacoes']
            df_geral = pd.DataFrame({
                'Categoria': ['Teve dispensação nos últimos 12 meses', 
                              'Não teve dispensação nos últimos 12 meses', 
                              'Em PrEP atualmente', 
                              'Estão descontinuados'],
                'Total': [c['Disp_Ultimos_12m'], c['Disp_Ultimos_12m_Nao'], c['EmPrEP_Atual'], c['Descontinuados']]
            })
            df_geral.to_excel(writer, sheet_name='Geral', index=False, startrow=0)

        # 2. Aba Em PrEP por ano
        if 'historico' in metrics_dict:
            metrics_dict['historico'].to_excel(writer, sheet_name='Em PrEP por ano', index=False)

        # 3. Aba Disp_total
        if 'disp_mes_ano' in metrics_dict:
            metrics_dict['disp_mes_ano'].to_excel(writer, sheet_name='Disp_total', index=True)

        # 4. Aba Novos usuários
        if 'novos_usuarios' in metrics_dict:
            metrics_dict['novos_usuarios'].to_excel(writer, sheet_name='Novos usuários', index=True)

        # 5. Aba Populações (em PrEP)
        if 'populacoes' in metrics_dict:
            metrics_dict['populacoes'].to_excel(writer, sheet_name='Populações (em PrEP)', index=False)

    print("Excel gerado com sucesso!")
    return filepath
