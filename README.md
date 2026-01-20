# Monitoramento PrEP - Guia de Uso (Walkthrough)

Este projeto realiza o processamento e monitoramento dos dados de PrEP, consolidando bases de dispensação e cadastro.

## 1. Execução do Script Principal

O script agora utiliza um sistema de **Cache Inteligente**.
- **1ª Execução do dia:** Baixa os dados da rede (Pode levar ~10 minutos). Salva uma cópia local na pasta `.cache`.
- **Execuções Seguintes:** Lê da cópia local (Leva ~10 segundos).

### Comando Padrão (Usa Cache se existir):
```powershell
python -m src.main --data_fechamento AAAA-MM-DD
```
*Exemplo:* `python -m src.main --data_fechamento 2025-09-30`

### Forçar Atualização (Ignorar Cache):
Se você atualizou os arquivos na rede e precisa processar novamente **no mesmo dia**, use a flag `--no_cache`:
```powershell
python -m src.main --data_fechamento 2025-09-30 --no_cache
```

---

## 2. Checagem Rápida de Dados (Frequência)
Após gerar o arquivo `df_prep_consolidado.csv`, você pode consultar frequências de colunas específicas rapidamente usando o script `check_data.py`.

### Exemplos de Uso:

**Frequência Simples:**
```powershell
python check_data.py ano_disp
```

**Filtrando apenas por quem não possui data de óbito:**
```powershell
python check_data.py ano_disp --filter "data_obito.isna()"
```

**Filtrando meses de um ano específico (Ex: 2024):**
```powershell
python check_data.py mes_disp --filter "ano_disp == 2024"
```

---

## 3. Notas de Performance
- O sistema foi otimizado para reduzir o tempo de processamento de **1 minuto para 5 segundos** usando cálculo vetorial.
- O maior tempo de espera é a leitura da rede (`V:/...`). O uso do cache resolve isso para testes repetidos.