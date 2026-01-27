import os
import sys

# Define the content
title = "Relatório de Análise Cruzada: PrEP e Início de TARV"
date_str = "23 de janeiro de 2026"

content_blocks = [
    ("1. Resumo Geral", 
     "Total de usuários identificados na intersecção entre as bases de PrEP e TARV (PVHA): 7.377 usuários.\n" 
     "O cruzamento foi realizado utilizando o identificador único 'Cod_unificado'."),
    
    ("2. Classificação Temporal", 
     "Analisamos a relação cronológica entre a Última Dispensa de PrEP e a Primeira Dispensa de TARV:\n\n" 
     "A) Conversão Pós-PrEP (Provável Soroconversão após abandono)\n" 
     "   - Quantidade: 4.838 (65,6% do total)\n" 
     "   - Definição: A primeira dispensa de TARV ocorreu APÓS a data da última dispensa de PrEP registrada.\n" 
     "   - Insight: A maioria desses casos (54%) iniciou TARV mais de 1 ano após ter parado a PrEP, sugerindo que o abandono da estratégia precede a infecção em longo prazo.\n\n" 
     "B) Inconsistências (TARV Antes ou Durante a PrEP)\n" 
     "   - Quantidade: 752 (10,2% do total)\n" 
     "   - Erro Crítico (TARV anterior à PrEP): 604 casos (8,2%). Usuários com registro de TARV anterior à primeira dispensa de PrEP.\n" 
     "   - Sobreposição (TARV durante a PrEP): 148 casos (2,0%). Usuários que iniciaram TARV no intervalo entre o início e o fim da PrEP.\n\n" 
     "C) Não Classificados\n" 
     "   - Quantidade: ~1.787 (24,2%)\n" 
     "   - Motivo: Datas de dispensa ausentes impediram o cálculo exato."),
    
    ("3. Distribuição do Tempo (Apenas Grupo Pós-PrEP)",
     "Análise do intervalo em dias entre a Última Dispensa de PrEP e a Primeira Dispensa de TARV (para os 4.838 casos válidos):\n\n" 
     "Estatísticas:\n" 
     "   - Média: 532 dias (~1 ano e meio)\n" 
     "   - Mediana: 408 dias\n\n" 
     "Distribuição por Faixas de Tempo:\n" 
     "   - < 1 mês:       200 (4,1%)  [Alerta: Possível falha de PrEP ou infecção aguda logo após parada]\n" 
     "   - 1 a 3 meses:   458 (9,5%)\n" 
     "   - 3 a 6 meses:   535 (11,1%)\n" 
     "   - 6 a 12 meses: 1.003 (20,7%)\n" 
     "   - > 1 ano:      2.642 (54,6%) [Maior grupo: Abandono de longo prazo]"),
     
    ("4. Conclusão",
     "O padrão predominante indica que a soroconversão ocorre majoritariamente em indivíduos que abandonaram a PrEP há um tempo considerável (mais de 1 ano). " 
     "Isso reforça que o desafio principal é a retenção e o reengajamento de usuários que deixam de buscar a profilaxia. " 
     "As possíveis 'falhas' agudas ou infecções imediatas após a parada (menos de 1 mês) representam uma minoria pequena (~4%) dos casos.")
]

filename_docx = "Relatorio_Analise_PrEP_TARV.docx"
filename_md = "Relatorio_Analise_PrEP_TARV.md"
current_dir = os.getcwd()

try:
    import win32com.client
    
    print(f"Tentando criar Word Document via COM em: {current_dir} ...")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Add()
    
    # Title
    para = doc.Content.Paragraphs.Add()
    para.Range.Text = title
    para.Range.Font.Size = 16
    para.Range.Font.Bold = True
    para.Range.InsertParagraphAfter()
    
    # Date
    para = doc.Content.Paragraphs.Add()
    para.Range.Text = date_str + "\n"
    para.Range.InsertParagraphAfter()
    
    # Blocks
    for header, text in content_blocks:
        para = doc.Content.Paragraphs.Add()
        para.Range.Text = header
        para.Range.Font.Size = 12
        para.Range.Font.Bold = True
        para.Range.InsertParagraphAfter()
        
        para = doc.Content.Paragraphs.Add()
        para.Range.Text = text + "\n"
        para.Range.Font.Size = 11
        para.Range.Font.Bold = False
        para.Range.InsertParagraphAfter()
        
    abs_path = os.path.join(current_dir, filename_docx)
    doc.SaveAs(abs_path)
    doc.Close()
    word.Quit()
    print(f"Sucesso! Documento salvo como: {filename_docx}")

except Exception as e:
    print(f"Não foi possível criar o arquivo .docx via COM: {e}")
    print("Gerando arquivo Markdown alternativo...")
    
    with open(filename_md, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n")
        f.write(f"_{date_str}_")
        f.write("\n\n")
        for header, text in content_blocks:
            f.write(f"## {header}\n")
            f.write(f"{text}\n\n")
    print(f"Relatório salvo em formato texto/markdown: {filename_md}")
