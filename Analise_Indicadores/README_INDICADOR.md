# Status do Indicador PrEP:HIV (Novos Vinculados)

Este documento registra o estado atual do desenvolvimento do script `src/indicador_prep_hiv.py`, destinado a replicar o cálculo do indicador "Razão entre Usuários em PrEP e Novos Vinculados ao HIV".

**Última Atualização:** 21/01/2026 17:48
**Script Principal:** `src/indicador_prep_hiv.py`
**Arquivo de Saída:** `Indicador_PrEP_HIV_20260121_1748.xlsx`

## Metodologia Implementada

O script replica a lógica do notebook de referência (`Indicador_PrEP_Vinculados v1.07.ipynb`) com as seguintes premissas validadas:

### 1. Numerador (Usuários em PrEP Ativos)
*   **Base:** Histórico completo de dispensações (`tb_dispensas_esquemas_udm`) carregado do cache local (`.cache/*.pkl`).
*   **Filtros:**
    *   **Óbitos:** Excluídos usuários com data de óbito registrada na base cruzada de HIV/SIM.
    *   **PVHA:** **NÃO** são excluídos preventivamente pela data de diagnóstico. A exclusão ocorre naturalmente quando o usuário interrompe a PrEP (devido ao diagnóstico).
    *   **Modalidade:** **INCLUI** usuários de "PrEP Sob Demanda" (nenhum filtro de modalidade aplicado).
*   **Critério de Atividade (Mês de Referência):**
    *   Usuário possui uma dispensação válida cobrindo o fim do mês analisado (`valid_until >= fim_do_mês`).
    *   **Validade da Dispensa:** `Data Dispensa + (Soma das Durações no Dia * 1.4)`.
    *   **Retenção:** Usuário deve ter tido pelo menos uma dispensação nos últimos **12 meses** em relação ao mês analisado.
*   **Localização:**
    *   Prioridade: Código IBGE de **Residência** (do Cadastro).
    *   Fallback: Código IBGE da **UDM** (Serviço) se residência for nula.

### 2. Denominador (Novos Vinculados HIV - 6 Meses)
*   **Base:** Arquivo Parquet da rede (`PVHA_prim_ult.parquet`).
*   **Janela:** Soma dos novos vinculados nos últimos **6 meses** (janela móvel).
*   **Deduplicação:**
    *   Pacientes (`Cod_unificado`) são deduplicados **dentro da janela de 6 meses**.
    *   Critério de desempate: Em caso de múltiplos registros na janela, considera-se o **mais recente** (ordenação por data decrescente).
*   **Localização:** Código IBGE de Residência.

## Status da Validação (Julho/2025)

Os resultados obtidos estão muito próximos da referência, com variações marginais (< 1% em grandes centros):

| Município | Valor Referência (Seu) | Valor Calculado (Script) | Diferença |
| :--- | :--- | :--- | :--- |
| **São Paulo** | 15,19 | 15,26 | +0,07 |
| **Rio de Janeiro** | 6,20 | 6,22 | +0,02 |
| **Curitiba** | 6,76 | 6,74 | -0,02 |
| **Florianópolis** | 12,49 | 12,57 | +0,08 |
| **Aracaju** | 2,96 | 3,01 | +0,05 |
| **Belo Horizonte** | 7,48 | 7,44 | -0,04 |

## Próximos Passos (Investigação de Diferenças)

Para eliminar as diferenças residuais, investigar:

1.  **Precisão da Data de Validade:** Verificar se o notebook usa `>` ou `>=` na comparação com o fim do mês, e se considera horas/minutos. (Script atual: `>=` e normaliza datas para 00:00).
2.  **Base de Cache:** Confirmar se o cache `.pkl` (gerado pelo `main.py`) contém exatamente as mesmas dispensas do momento em que o notebook de referência foi rodado. Diferenças de atualização da base (retroativas) são a causa mais provável.
3.  **Filtro de Idade:** Verificar se existe algum filtro implícito de idade (ex: >= 15 anos) no numerador ou denominador que não foi detectado.
4.  **Tratamento de Mudança de Município:** Refinar a lógica de qual município é atribuído ao paciente no numerador quando ele muda de residência ao longo do tempo (atualmente usa a residência mais recente no cadastro, ou a da dispensa se usar histórico). *Nota: O script atual usa o dado do cadastro (estático) ou da dispensa (dinâmico)? Verifica-se que usa o merge com cadastro, o que pode ser estático.*

---
**Comando para Execução:**
```powershell
python src/indicador_prep_hiv.py --data_fechamento 2025-07-31
```
