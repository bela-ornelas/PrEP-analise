import datetime
import subprocess
import sys
import os

# Nome do arquivo de log que ficará na pasta do projeto
LOG_FILE = "historico_automacao.txt"

def log_msg(mensagem):
    """Escreve uma mensagem no arquivo de texto com data/hora."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {mensagem}\n")
    except Exception as e:
        # Se falhar ao escrever o log, tenta imprimir no console (útil para debug manual)
        print(f"Erro ao escrever no log: {e}")

def run_automation():
    hoje = datetime.date.today()
    
    # Calcular último dia do mês anterior
    primeiro_dia_deste_mes = hoje.replace(day=1)
    data_fechamento = primeiro_dia_deste_mes - datetime.timedelta(days=1)
    data_str = data_fechamento.strftime("%Y-%m-%d")
    
    log_msg("="*50)
    log_msg(f"INICIANDO EXECUÇÃO AUTOMÁTICA")
    log_msg(f"Data de Referência (Fechamento): {data_str}")
    
    # Comando para rodar o módulo principal
    cmd = [
        sys.executable, 
        "-m", "src.main", 
        "--data_fechamento", data_str,
        "--no_cache" # Força atualização da rede
    ]
    
    try:
        # Executa o script e captura a saída (stdout e stderr)
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            log_msg("STATUS: SUCESSO")
            log_msg("Resumo da execução:")
            # Pega apenas as últimas linhas relevantes do output para não poluir o log
            output_lines = resultado.stdout.strip().split('\n')
            relevant_lines = [line for line in output_lines if "Tempo total" in line or "Outputs salvos" in line or "Excel gerado" in line]
            
            if not relevant_lines:
                # Se não achou linhas específicas, grava as últimas 5
                relevant_lines = output_lines[-5:]
                
            for line in relevant_lines:
                log_msg(f"  > {line}")
        else:
            log_msg("STATUS: FALHA")
            log_msg("--- Erro capturado ---")
            log_msg(resultado.stderr)
            log_msg("----------------------")
            
    except Exception as e:
        log_msg(f"STATUS: ERRO CRÍTICO AO CHAMAR O SUBPROCESSO: {e}")

if __name__ == "__main__":
    run_automation()