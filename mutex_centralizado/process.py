import socket
import sys
import time
import argparse
import random
from datetime import datetime
from protocol import format_message, parse_message, MessageType, MESSAGE_SIZE

HOST = '127.0.0.1'
PORT = 5000

def run_process(process_id: int, r: int, k: int):
    # 1. Conectar ao coordenador
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((HOST, PORT))
        except ConnectionRefusedError:
            print("Não foi possível conectar ao coordenador.")
            return

        print(f"Processo {process_id} conectado ao coordenador.")

        # 3. Lógica de Execução: Um loop que executa R vezes
        for iteration in range(r):
            # Dormir aleatoriamente antes de fazer um request (3 a 4 segundos)
            sleep_time = random.uniform(3.0, 4.0)
            print(f"[{process_id}] Dormindo {sleep_time:.2f} segundos antes do REQUEST (Iteração {iteration + 1}/{r})")
            time.sleep(sleep_time)

            # a) Envia REQUEST ao coordenador.
            req_msg = format_message(MessageType.REQUEST, process_id)
            sock.sendall(req_msg.encode('utf-8'))
            print(f"[{process_id}] Enviou REQUEST (Iteração {iteration + 1}/{r})")

            # b) Aguarda de forma bloqueante a recepção do GRANT.
            # O recv vai bloquear a thread até receber os 16 bytes.
            data = sock.recv(MESSAGE_SIZE)
            if not data:
                print("Conexão fechada pelo coordenador.")
                break
                
            msg_str = data.decode('utf-8')
            msg_type, _ = parse_message(msg_str)
            
            if msg_type == MessageType.GRANT:
                print(f"[{process_id}] Recebeu GRANT")
                
                # c) Abre o arquivo 'resultado.txt' no modo APPEND.
                # d) Escreve uma linha com: ID_PROCESSO TIMESTAMP_SISTEMA_COM_MILISEGUNDOS.
                # e) Fecha o arquivo (resolvido automaticamente pelo 'with open').
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                with open("resultado.txt", "a", encoding="utf-8") as f:
                    f.write(f"{process_id} {timestamp}\n")
                
                # f) Executa sleep(K segundos).
                time.sleep(k)
                
                # g) Envia RELEASE ao coordenador.
                rel_msg = format_message(MessageType.RELEASE, process_id)
                sock.sendall(rel_msg.encode('utf-8'))
                print(f"[{process_id}] Enviou RELEASE")
            else:
                print(f"Tipo de mensagem inesperado recebido: {msg_type}")
                break

        print(f"Processo {process_id} finalizou todas as {r} iterações. Fechando conexão.")
        # 4. Após o loop, o processo encerra a conexão e fecha (tratado automaticamente pelo 'with socket').

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processo Cliente para Exclusão Mútua Centralizada")
    parser.add_argument("process_id", type=int, help="ID do processo")
    parser.add_argument("r", type=int, help="Número de repetições (R)")
    parser.add_argument("k", type=int, help="Tempo de espera na seção crítica em segundos (K)")
    
    args = parser.parse_args()
    
    run_process(args.process_id, args.r, args.k)
