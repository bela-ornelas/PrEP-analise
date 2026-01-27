import json
import os

def gerar_notebook_final():
    input_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados v1.07.ipynb'
    output_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados_v1.08.ipynb'
    
    print(f"Lendo original: {input_path}...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo original '{input_path}' não encontrado.")
        return

    new_cells = []
    
    # --- Configuração da Nova Célula de Carga ---
    # Usa aspas simples para delimitar a string Python e aspas duplas no código interno
    new_load_source = [
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
    
    new_load_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": new_load_source
    }

    # --- Padrões de Corte ---
    start_cut_pattern = "prep.carregar_bases"
    end_cut_pattern = "pri_disp_anos = PrEP.groupby"
    
    # --- Padrões de Substituição de Texto (Cad -> PrEP) ---
    replacements = [
        {
            "old": 'PrEP_historico = pd.merge(Disp_semdupl,Cad, on="codigo_pac_eleito", how="left", suffixes=(_disp,""))',
            "new": [
                '# Substituindo Cad por PrEP (que já contém demografia)\n',
                'PrEP_historico = pd.merge(Disp_semdupl, PrEP, on="codigo_pac_eleito", how="left", suffixes=(_disp,""))'
            ]
        },
        {
            "old": 'PrEP_historico_mun = pd.merge(Disp_semdupl,Cad, on="codigo_pac_eleito", how="left", suffixes=(_disp,""))',
            "new": [
                '# Substituindo Cad por PrEP\n',
                'PrEP_historico_mun = pd.merge(Disp_semdupl, PrEP, on="codigo_pac_eleito", how="left", suffixes=(_disp,""))'
            ]
        }
    ]

    skip = False
    found_start = False
    found_end = False
    
    total_text_replacements = 0

    for i, cell in enumerate(nb['cells']):
        source_list = cell.get('source', [])
        source_str = "".join(source_list)
        
        # 1. Lógica de Corte (Remover carga antiga)
        if not found_start and start_cut_pattern in source_str:
            print(f"Substituindo bloco de carga na célula {i}")
            found_start = True
            skip = True
            new_cells.append(new_load_cell)
            continue

        if skip and end_cut_pattern in source_str:
            print(f"Fim do corte encontrado na célula {i}")
            found_end = True
            skip = False
            # A célula atual (onde o corte termina) DEVE ser incluída e processada
        
        if skip:
            continue

        # 2. Lógica de Substituição de Texto (Cad -> PrEP)
        if cell['cell_type'] == 'code':
            new_source_list = []
            modified_cell = False
            
            for line in source_list:
                line_replaced = False
                for rep in replacements:
                    if rep['old'].strip() in line.strip():
                        indent_size = line.find(rep['old'].strip()[0])
                        indent = line[:indent_size] if indent_size >= 0 else ""
                        
                        for nl in rep['new']:
                            new_source_list.append(indent + nl + "\n")
                        
                        line_replaced = True
                        modified_cell = True
                        total_text_replacements += 1
                        break
                
                if not line_replaced:
                    new_source_list.append(line)
            
            if modified_cell:
                cell['source'] = new_source_list
        
        new_cells.append(cell)

    if found_start and found_end:
        nb['cells'] = new_cells
        
        # Atualizar metadados básicos
        if "metadata" in nb:
            nb["metadata"]["kernelspec"] = {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }

        print(f"Salvando {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Sucesso! {total_text_replacements} referências a 'Cad' corrigidas.")
    else:
        print("ERRO CRÍTICO: Não foi possível localizar o intervalo de células para substituição.")
        print(f"Início encontrado: {found_start}")
        print(f"Fim encontrado: {found_end}")

if __name__ == "__main__":
    gerar_notebook_final()
