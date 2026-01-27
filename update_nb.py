import json
import os

def atualizar_notebook():
    input_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados v1.07.ipynb'
    output_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados_v1.08.ipynb'
    
    print(f"Lendo {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    new_cells = []
    skip = False
    
    # Nova célula de código (Usando aspas simples para delimitar a string Python, aspas duplas dentro do código)
    new_source = [
        '# --- CARREGAMENTO OTIMIZADO (Via Parquets) ---\n',
        '# Substitui o carregamento de múltiplas bases e processamentos pesados\n',
        '\n',
        'print("Carregando bases PrEP (Consolidado e Dispensas)...")\n',
        '\n',
        '# 1. Base Consolidada (Uma linha por paciente)\n',
        'PrEP = pd.read_parquet("//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PrEP_unico.parquet")\n',
        '\n',
        '# 2. Base de Dispensas (Histórico)\n',
        'Disp_semdupl = pd.read_parquet("//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PrEP_dispensas.parquet")\n',
        '\n',
        '# --- AJUSTES DE COMPATIBILIDADE ---\n',
        '\n',
        '# Ajustes de tipos em PrEP\n',
        'if "codigo_ibge_resid" in PrEP.columns:\n',
        '    PrEP["codigo_ibge_resid"] = pd.to_numeric(PrEP["codigo_ibge_resid"], errors="coerce").fillna(0).astype(int)\n',
        'if "cod_ibge_udm" in PrEP.columns:\n',
        '    PrEP["cod_ibge_udm"] = pd.to_numeric(PrEP["cod_ibge_udm"], errors="coerce").fillna(0).astype(int)\n',
        '\n',
        '# Garantir datetime em PrEP\n',
        'date_cols_prep = ["dt_disp", "dt_disp_min", "dt_disp_max", "data_nascimento"]\n',
        'for col in date_cols_prep:\n',
        '    if col in PrEP.columns:\n',
        '        PrEP[col] = pd.to_datetime(PrEP[col], errors="coerce")\n',
        '\n',
        '# Garantir datetime em Disp_semdupl\n',
        'date_cols_disp = ["dt_disp", "data_dispensa"]\n',
        'for col in date_cols_disp:\n',
        '    if col in Disp_semdupl.columns:\n',
        '        Disp_semdupl[col] = pd.to_datetime(Disp_semdupl[col], errors="coerce")\n',
        '\n',
        'print("Bases carregadas.")\n',
        'print(f"PrEP (Consolidado): {len(PrEP)} linhas")\n',
        'print(f"Disp_semdupl (Dispensas): {len(Disp_semdupl)} linhas")'
    ]
    
    new_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": new_source
    }

    start_pattern = "prep.carregar_bases"
    end_pattern = "pri_disp_anos = PrEP.groupby"
    
    found_start = False
    found_end = False

    for i, cell in enumerate(nb['cells']):
        source_str = "".join(cell.get('source', []))
        
        # Lógica de início de corte
        if not found_start and start_pattern in source_str:
            print(f"Encontrado início de substituição na célula {i}")
            found_start = True
            skip = True
            new_cells.append(new_cell)
            continue

        # Lógica de fim de corte
        if skip and end_pattern in source_str:
            print(f"Encontrado fim de substituição na célula {i}")
            found_end = True
            skip = False
            # Não continue, adiciona a célula atual (que contém o end_pattern)
        
        if not skip:
            new_cells.append(cell)

    if found_start and found_end:
        nb['cells'] = new_cells
        
        # Atualizar metadados se necessário (opcional)
        if "metadata" in nb:
            nb["metadata"]["kernelspec"] = {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }

        print(f"Salvando novo notebook em {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("Concluído com sucesso!")
    else:
        print("ERRO: Não foi possível encontrar os padrões de início ou fim.")
        print(f"Início encontrado: {found_start}")
        print(f"Fim encontrado: {found_end}")

if __name__ == "__main__":
    atualizar_notebook()
