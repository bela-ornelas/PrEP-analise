# Análise de Indicadores PrEP:HIV

Este diretório contém as ferramentas para geração e monitoramento do indicador **Razão entre Usuários em PrEP e Novos Vinculados ao HIV**.

## 📂 Estrutura de Arquivos

*   **`gerar_indicador_prep_otimizado.py`**: Script principal (versão otimizada) que realiza o cálculo do indicador.
*   **`README.md`**: Este arquivo de documentação.

---

## 📊 Metodologia do Indicador

O indicador busca avaliar a cobertura da PrEP em relação à incidência de novos casos de HIV (proxy: novos vinculados).

### 1. Numerador: Usuários em PrEP (`Em PrEP`)
*   **Fonte:** Arquivo consolidado `PrEP_unico.parquet` (gerado pelo pipeline principal).
*   **Definição:** Usuários marcados estritamente como **"Em PrEP atualmente"** na coluna `EmPrEP_Atual`.
*   **Geografia:** Município de residência (`codigo_ibge_resid`). Se nulo, utiliza-se o município da unidade dispensadora (`cod_ibge_udm`).

### 2. Denominador: Novos Vinculados (`Vinculados`)
*   **Fonte:** Arquivo `PVHA_prim_ult.parquet` (Base SP-SADT/SISCEL).
*   **Definição:** Pessoas vivendo com HIV/Aids (PVHA) cuja primeira evidência de vínculo (exame CD4/CV ou dispensa TARV) ocorreu nos **últimos 6 meses** em relação à data de fechamento.
*   **Geografia:** Município de residência.

### 3. Cálculo
$$
\text{Indicador} = \frac{\text{Usuários em PrEP Atualmente}}{\text{Novos Vinculados (últimos 6 meses)}}
$$

---

## 🚀 Como Executar

O script foi desenhado para rodar via linha de comando (CLI), lendo os arquivos `.parquet` diretamente da rede ou disco local mapeado.

### Pré-requisitos
*   Python 3.x instalado.
*   Bibliotecas: `pandas`, `openpyxl`, `pyarrow`, `numpy`.
*   Acesso aos drives de rede mapeados (`M:` e `V:`) ou caminhos configurados.

### Comando

Navegue até esta pasta e execute:

```bash
python gerar_indicador_prep_otimizado.py --data_fechamento AAAA-MM-DD
```

**Exemplo:**
```bash
python gerar_indicador_prep_otimizado.py --data_fechamento 2025-12-31
```

O script irá:
1.  Carregar as bases (`PrEP_unico.parquet`, `PrEP_dispensas.parquet`, `PVHA_prim_ult.parquet`).
2.  Calcular os totais atuais por Município, Estado e Região.
3.  Calcular a série histórica mensal.
4.  Exibir uma conferência no terminal (Dados de Brasília e Totais Nacionais).
5.  Salvar o arquivo Excel final.

---

## 📤 Saída (Output)

O script gera um arquivo Excel (`Indicador_PrEP_MM_AAAA.xlsx`) salvo em `V:\2026\Monitoramento e Avaliação\DOCUMENTOS\PrEP\Indicador PrEP HIV` contendo as abas:

1.  **Geral:** Tabelas resumo (contagem de municípios por faixa do indicador).
2.  **Município:** Lista completa de todos os municípios, população, nº em PrEP, nº Vinculados, valor do Indicador e Grupo.
3.  **Município_50k:** Mesmo que o anterior, filtrado para municípios com >50k habitantes.
4.  **UF:** Agregado por Unidade Federativa.
5.  **Região:** Agregado por Região (Ordem: Norte, Nordeste, Sudeste, Sul, Centro-Oeste).
6.  **Nacional:** Totais Brasil.
7.  **Mensal_municipio:** Histórico mês a mês do indicador para cada município (Jan/2022 até data atual).

---

## 🛠️ Manutenção

*   **Classificação de Grupos:**
    *   *Sem novos vinculados e sem PrEP*
    *   *Sem novos vinculados, com pessoas em PrEP*
    *   *Grupo 0* (Indicador < 1)
    *   *Grupo 1* (1 <= Indicador < 2)
    *   *Grupo 2* (2 <= Indicador < 3)
    *   *Grupo 3* (3 <= Indicador < 4)
    *   *Grupo 4* (Indicador >= 4)
