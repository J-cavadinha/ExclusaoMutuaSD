import os
import sys
import time
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Orquestrador do Teste de Exclusão Mútua Centralizada")
    parser.add_argument("N", type=int, nargs="?", default=3, help="Número de processos clientes (N)")
    parser.add_argument("R", type=int, nargs="?", default=2, help="Número de repetições por processo (R)")
    parser.add_argument("K", type=int, nargs="?", default=1, help="Tempo de espera na seção crítica em segundos (K)")
    args = parser.parse_args()

    n, r, k = args.N, args.R, args.K

    print("==================================================")
    print(" Iniciando Teste de Exclusão Mútua Centralizada")
    print(f" Processos (N): {n} | Repetições (R): {r} | Espera (K): {k} seg")
    print("==================================================")

    # [1] Limpando arquivos antigos
    print("[1] Limpando arquivos antigos...")
    for filename in ["coordinator.log", "resultado.txt"]:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Erro ao remover {filename}: {e}")

    # [2] Iniciando Coordenador
    print("[2] Iniciando Coordenador em background...")
    log_file = open("coordinator.log", "w", encoding="utf-8")
    
    # Executa com python -u para desativar buffer de saída
    coord_proc = subprocess.Popen(
        [sys.executable, "-u", "coordinator.py"],
        stdin=subprocess.PIPE,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Aguarda 1 segundo para garantir que o socket do coordenador esteja online
    time.sleep(1)

    # [3] Iniciando N processos simultaneamente
    print(f"[3] Iniciando {n} processos simultaneamente...")
    processes = []
    for i in range(1, n + 1):
        proc = subprocess.Popen(
            [sys.executable, "-u", "process.py", str(i), str(r), str(k)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(proc)

    # [4] Aguardando a execução dos processos
    print("[4] Aguardando a execução dos processos...")
    for proc in processes:
        proc.wait()

    # [5] Processos finalizados. Encerrando o coordenador
    print("[5] Processos finalizados. Encerrando o coordenador...")
    
    # Tenta encerrar o coordenador via comando de saída da UI
    try:
        coord_proc.stdin.write("3\n")
        coord_proc.stdin.flush()
        coord_proc.wait(timeout=2)
    except Exception:
        # Se falhar ou demorar, força a terminação
        coord_proc.terminate()
        try:
            coord_proc.wait(timeout=2)
        except Exception:
            coord_proc.kill()

    log_file.close()

    print("==================================================")
    print(" Execução concluída. Arquivos gerados:")
    print(" - resultado.txt")
    print(" - coordinator.log")
    print("==================================================")

if __name__ == "__main__":
    main()
