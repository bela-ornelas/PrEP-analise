import json

def fix_final():
    input_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados_v1.08.ipynb'
    
    print(f"Lendo {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    count = 0
    
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source_list = cell.get('source', [])
            new_source_list = []
            modified = False
            
            for line in source_list:
                # Substituição robusta e simples
                if "pd.merge(Disp_semdupl,Cad" in line:
                    new_line = line.replace("pd.merge(Disp_semdupl,Cad", "pd.merge(Disp_semdupl, PrEP")
                    new_source_list.append(new_line)
                    count += 1
                    modified = True
                else:
                    new_source_list.append(line)
            
            if modified:
                cell['source'] = new_source_list

    print(f"Substituições realizadas: {count}")
    
    print(f"Sobrescrevendo {input_path}...")
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Concluído!")

if __name__ == "__main__":
    fix_final()
