import pandas as pd
import os

def export_to_excel(output_dir, data_fechamento, metrics_dict):
    """
    Gera um NOVO arquivo Excel de monitoramento com todas as abas.
    """
    data_dt = pd.to_datetime(data_fechamento)
    mes = data_dt.month
    ano = data_dt.year
    
    filename = f"Monitoramento_PrEP_{mes:02d}_{ano}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    print(f"Gerando NOVO arquivo Excel em: {filepath}")
    
    # Criar novo arquivo (mode='w')
    with pd.ExcelWriter(filepath, engine='openpyxl', mode='w') as writer:
        # 1. Aba Geral
        if 'classificacoes' in metrics_dict:
            c = metrics_dict['classificacoes']
            df_geral = pd.DataFrame({
                'Categoria': ['Procuraram PrEP',
                              'Iniciaram PrEP',
                              'Teve dispensação nos últimos 12 meses', 
                              'Não teve dispensação nos últimos 12 meses', 
                              'Em PrEP atualmente', 
                              'Estão descontinuados'],
                'Total': [c.get('Procuraram_PrEP', 0),
                          c.get('Iniciaram_PrEP', 0),
                          c['Disp_Ultimos_12m'], 
                          c['Disp_Ultimos_12m_Nao'], 
                          c['EmPrEP_Atual'], 
                          c['Descontinuados']]
            })
            df_geral.to_excel(writer, sheet_name='Geral', index=False)

        # 2. Aba Em PrEP_mes_ano (Histórico Mensal Detalhado)
        if 'historico' in metrics_dict:
            metrics_dict['historico'].to_excel(writer, sheet_name='Em PrEP_mes_ano', index=False)

        # 3. Aba Em PrEP por ano (Resumo Anual) - NOVA
        if 'annual_summary' in metrics_dict:
            metrics_dict['annual_summary'].to_excel(writer, sheet_name='Em PrEP por ano', index=False)

        # 4. Aba Disp_total
        if 'disp_mes_ano' in metrics_dict:
            metrics_dict['disp_mes_ano'].to_excel(writer, sheet_name='Disp_total', index=True)

        # 5. Aba Novos usuários
        if 'novos_usuarios' in metrics_dict:
            metrics_dict['novos_usuarios'].to_excel(writer, sheet_name='Novos usuários', index=True)

        # 6. Aba Populações (em PrEP)
        if 'populacoes' in metrics_dict:
            metrics_dict['populacoes'].to_excel(writer, sheet_name='Populações (em PrEP)', index=False)

    print("Excel gerado com sucesso!")
    return filepath
