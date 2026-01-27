import json

def fix_na_prep_historico():
    input_path = 'Arquivos_consulta/Indicador_PrEP_Vinculados_v1.08.ipynb'
    
    print(f"Lendo {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    count = 0
    # Critérios de busca mais flexíveis
    search_terms = ["PrEP_historico", "=", "pd.merge", "Disp_semdupl", "PrEP"]
    
    fix_line = 'PrEP_historico["codigo_ibge_resid"] = pd.to_numeric(PrEP_historico["codigo_ibge_resid"], errors="coerce").fillna(0).astype(int)'

    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source_list = cell.get('source', [])
            new_source_list = []
            modified = False
            
            for line in source_list:
                new_source_list.append(line)
                
                # Verifica se todos os termos estão na linha
                if all(term in line for term in search_terms):
                    # Evita duplicar a correção se já existir
                    if len(source_list) > source_list.index(line) + 2:
                         next_lines = "".join(source_list[source_list.index(line)+1:source_list.index(line)+5])
                         if "codigo_ibge_resid" in next_lines and "fillna(0)" in next_lines:
                             print("Correção já parece existir. Pulando.")
                             continue

                    print(f"Encontrado alvo: {line.strip()}")
                    new_source_list.append('\n')
                    new_source_list.append('# Correção para evitar TypeError no np.select devido a NaNs ou tipos mistos após o merge\n')
                    new_source_list.append(fix_line + '\n')
                    count += 1
                    modified = True
            
            if modified:
                cell['source'] = new_source_list

    if count > 0:
        print(f"Inserida correção de NaNs em {count} locais.")
        print(f"Sobrescrevendo {input_path}...")
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("Concluído!")
    else:
        print("ERRO: Não foi possível localizar a linha de merge para inserir a correção.")

if __name__ == "__main__":
    fix_na_prep_historico()