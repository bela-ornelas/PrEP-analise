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
- **Em PrEP por ano:** Tabela resumo anual com contagens e % de retenção (2018-Atual).
- **Dados por UF:** Resumo geográfico por Região e Estado, com totais de dispensas e pacientes ativos.
- **Em PrEP_mes_ano:** Histórico detalhado mês a mês de usuários ativos e descontinuados.
- **Disp_total:** Matriz de dispensações totais por mês e ano.
- **Novos usuários:** Matriz de novos usuários (primeira dispensa) por mês e ano.
- **Populações (em PrEP):** Perfil sociodemográfico (População Chave, Faixa Etária, Escolaridade e Raça) dos usuários ativos.

### B. Gráficos (PNG):
- **`PrEP_disp.png`:** Histórico mensal de dispensas totais.
- **`PrEP_cascata.png`:** Cascata/Funil do cuidado PrEP (da procura à adesão).
- **`PrEP_emprep.png`:** Comparativo anual de usuários com dispensa vs. usuários que permaneceram em PrEP (inclui % de retenção).
- **`PrEP_novosusuarios.png`:** Histórico de novos usuários com anotações de marcos históricos (Pandemia, Teleatendimento, etc.).

### C. Base de Dados: `df_prep_consolidado.csv`
- Arquivo CSV (separado por `;`) contendo **uma linha por paciente**.
- Base rica com dados demográficos, datas da primeira e última dispensa, e flags de status.
- Ideal para ser importada em ferramentas de BI (PowerBI, Tableau) ou para conferências rápidas.

---

## 3. Ferramenta de Consulta Rápida
Para consultar frequências na base consolidada sem abrir o Excel ou rodar o script novamente:
```powershell
python check_data.py nome_da_coluna
```
*Exemplo:* `python check_data.py fetar --filter "EmPrEP_Atual == 'Em PrEP atualmente'"`

---

## 4. Notas Técnicas
- **Performance:** O motor de cálculo histórico foi otimizado com NumPy, reduzindo o tempo de processamento lógico de minutos para poucos segundos.
- **Consistência:** Os números do terminal, do Excel e dos Gráficos são extraídos da mesma base consolidada (`df_prep`), garantindo integridade total dos dados.
