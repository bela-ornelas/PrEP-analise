import json
import os

def fix_prep_historico():
    input_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados_v1.09.ipynb'
    output_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados_v1.10.ipynb'
    
    if not os.path.exists(input_path):
        print(f"ERRO: Arquivo {input_path} não encontrado.")
        return

    print(f"Lendo {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # Padrões para substituição
    # Note: O script original usava Cad como segunda base no merge
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

    count_replaced = 0
    
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source_list = cell.get('source', [])
            new_source_list = []
            modified_cell = False
            
            for line in source_list:
                line_replaced = False
                for rep in replacements:
                    if rep['old'].strip() in line.strip():
                        # Identificar indentação
                        indent_size = line.find(rep['old'].strip()[0])
                        indent = line[:indent_size] if indent_size >= 0 else ""
                        
                        for nl in rep['new']:
                            new_source_list.append(indent + nl + "\n")
                        
                        line_replaced = True
                        count_replaced += 1
                        modified_cell = True
                        break
                
                if not line_replaced:
                    new_source_list.append(line)
            
            if modified_cell:
                cell['source'] = new_source_list

    print(f"Total de substituições realizadas: {count_replaced}")
    
    if count_replaced > 0:
        print(f"Salvando novo notebook em {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("Concluído!")
    else:
        print("Nenhum padrão encontrado para substituição. Verifique se o notebook já foi alterado ou se os nomes batem.")

if __name__ == "__main__":
    fix_prep_historico()