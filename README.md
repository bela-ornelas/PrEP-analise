# Monitoramento PrEP - Guia de Uso (Walkthrough)

Este projeto realiza o processamento e monitoramento dos dados de PrEP, consolidando bases de dispensação e cadastro em um ambiente otimizado.

## 1. Execução do Script Principal

O script utiliza um sistema de **Cache Inteligente** para contornar a lentidão de leitura em drives de rede.
- **1ª Execução do dia:** Baixa os dados da rede (Pode levar ~8-10 minutos). Salva uma cópia local na pasta `.cache`.
- **Execuções Seguintes:** Lê da cópia local (Leva ~10 segundos).

### Comando Padrão:
```powershell
python -m src.main --data_fechamento AAAA-MM-DD
```
*Exemplo:* `python -m src.main --data_fechamento 2025-12-31`

### Forçar Atualização (Ignorar Cache):
Use a flag `--no_cache` se os arquivos na rede forem atualizados no mesmo dia:
```powershell
python -m src.main --data_fechamento 2025-12-31 --no_cache
```

---

## 2. Descrição dos Outputs (Resultados)

Ao final da execução, os arquivos serão salvos por padrão em:
`V:\2026\Monitoramento e Avaliação\DOCUMENTOS\PrEP\Dados_automaticos`

### A. Planilha Excel: `Monitoramento_PrEP_MM_AAAA.xlsx`
Contém as seguintes abas:
- **Geral:** Totais consolidados (Procuraram, Iniciaram, Disp 12m, Em PrEP e Descontinuados).
- **Disp_total:** Matriz de dispensações totais por mês e ano.
- **Novos usuários:** Matriz de novos usuários (primeira dispensa) por mês e ano.
- **Em PrEP por ano:** Tabela resumo anual com contagens e % de retenção (2018-Atual).
- **Em PrEP_mes_ano:** Histórico detalhado mês a mês de usuários ativos e descontinuados.
- **Populações (em PrEP):** Perfil sociodemográfico (População Chave, Faixa Etária, Escolaridade e Raça) dos usuários ativos.
- **Dados por UF:** Resumo geográfico por Região e Estado.
- **Mun:** Resumo detalhado por Município e Serviço de Saúde.

### B. Gráficos (PNG) e PowerPoint:
- **`Monitoramento_PrEP_MM_AAAA.pptx`:** Apresentação completa gerada automaticamente.
- Imagens individuais: `PrEP_disp.png`, `PrEP_cascata.png`, `PrEP_emprep.png`, `PrEP_novosusuarios.png`, etc.

### C. Base de Dados: `df_prep_consolidado.csv`
- Arquivo CSV contendo **uma linha por paciente**.

---

## 3. Ferramenta de Consulta Rápida
Para consultar frequências na base consolidada sem abrir o Excel:
```powershell
python check_data.py fetar --filter "EmPrEP_Atual == 'Em PrEP atualmente'"
```

---

## 4. Notas Técnicas
- **Performance:** O motor de cálculo histórico foi otimizado com NumPy.
- **Consistência:** Os números do terminal, do Excel e dos Gráficos são extraídos da mesma base consolidada (`df_prep`).

---

## 5. Modos de Execução (Interatividade e Automação)

O script suporta diferentes modos de operação para flexibilidade:

1.  **Interatividade (Padrão):** Se rodar sem flags especiais, o script perguntará se você deseja gerar o Excel e o PowerPoint.
    ```powershell
    python -m src.main --data_fechamento 2025-12-31
    # Pergunta: Gerar Excel? [S/n]
    ```

2.  **Automação Total (`--auto`):** Pula todas as perguntas e gera tudo (ideal para agendador de tarefas).
    ```powershell
    python -m src.main --data_fechamento 2025-12-31 --auto
    ```

3.  **Controle Fino:** Você pode forçar ou pular etapas específicas.
    *   `--skip_excel`: Não gera a planilha.
    *   `--skip_ppt`: Não gera a apresentação.
    *   `--no_cache`: Força download da rede.