# Análise de Indicadores PrEP:HIV

Este diretório contém as ferramentas para geração e monitoramento do indicador **Razão entre Usuários em PrEP e Novos Vinculados ao HIV**.

## 📂 Estrutura de Arquivos

*   **`indicador_prep_hiv.py`**: Script principal (orquestrador) que realiza o cálculo do indicador e gera os relatórios.
*   **`visualizacao.py`**: Módulo responsável pela geração de gráficos (Matplotlib) e testes estatísticos (Mann-Kendall).
*   **`sociodemografico.py`**: Módulo para análises de recorte populacional (Raça/Cor, Faixa Etária, etc.).
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

O script foi desenhado para rodar via linha de comando (CLI).

### Pré-requisitos
*   Python 3.x instalado.
*   Bibliotecas: `pandas`, `openpyxl`, `pyarrow`, `numpy`, `matplotlib`, `scikit-learn`, `pymannkendall`.
*   Acesso aos drives de rede mapeados (`M:` e `V:`) ou caminhos configurados.

### Comando

Navegue até esta pasta e execute:

```bash
python indicador_prep_hiv.py --data_fechamento AAAA-MM-DD
```

**Exemplo:**
```bash
python indicador_prep_hiv.py --data_fechamento 2025-12-31
```

O script irá:
1.  Carregar as bases (`PrEP_unico`, `PrEP_dispensas`, `PVHA_prim_ult`).
2.  Calcular indicadores atuais e séries históricas (Município, UF, Região, Brasil).
3.  Gerar relatórios Excel detalhados.
4.  Executar testes de tendência (Mann-Kendall) para identificar crescimento/queda.
5.  Gerar gráficos de séries históricas e tendências lineares.
6.  Realizar análise sociodemográfica (Raça/Cor).

---

## out Saída (Output)

Os arquivos são salvos em `V:\2026\Monitoramento e Avaliação\DOCUMENTOS\PrEP\Indicador PrEP HIV`.

### 1. Relatório Geral (`Indicador_PrEP_MM_AAAA.xlsx`)
*   **Geral:** Tabelas resumo.
*   **Município / UF / Região / Nacional:** Dados detalhados.
*   **Mensal_municipio / Mensal_BR:** Histórico mês a mês.
*   **Mann_Kendall:** Resultados estatísticos de tendência.
*   **Raca_Cor:** Indicador atual segmentado por autodeclaração de raça.

### 2. Relatório AHA (`AHA\Indicador_PrEP_AHA_...xlsx`)
*   Focado nas capitais selecionadas (Campo Grande, Curitiba, Florianópolis, Fortaleza, Porto Alegre) + Brasil.
*   Inclui gráficos específicos e teste de tendência.

### 3. Gráficos (`Graficos\`)
*   Séries históricas comparativas.
*   Linhas de tendência (últimos 12 ou 18 meses).
*   Gráficos sociodemográficos.

---

## 🛠️ Manutenção

*   **Ordem das Regiões:** Fixada no código como `['Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']`.
*   **Classificação de Grupos:**
    *   *Sem novos vinculados e sem PrEP*
    *   *Sem novos vinculados, com pessoas em PrEP*
    *   *Grupo 0* (Indicador < 1)
    *   *Grupo 1* (1 <= Indicador < 2)
    *   *Grupo 2* (2 <= Indicador < 3)
    *   *Grupo 3* (3 <= Indicador < 4)
    *   *Grupo 4* (Indicador >= 4)