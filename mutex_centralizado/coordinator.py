import socket
import threading
import time
import sys
from datetime import datetime

from protocol import format_message, parse_message, MessageType, MESSAGE_SIZE
from coordinator_state import CoordinatorState

HOST = '127.0.0.1'
PORT = 5000
COORDINATOR_ID = 0

class Coordinator:
    def __init__(self):
        self.state = CoordinatorState()
        self.is_cs_free = True
        self.cs_lock = threading.Lock()
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True

    def log(self, msg_type: str, src: int, dest: int):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"\n[{timestamp}] - [{msg_type}] - [{src}] -> [{dest}]")

    
    #Thread de rede (recebe mensagens)
    def handle_client(self, conn: socket.socket, addr):
        try:
            while self.running:
                data = conn.recv(MESSAGE_SIZE)
                if not data:
                    break
                
                try:
                    msg_str = data.decode('utf-8')
                    msg_type, process_id = parse_message(msg_str)
                except Exception as e:
                    print(f"Erro ao decodificar mensagem de {addr}: {e}")
                    continue

                self.state.add_connection(process_id, conn, addr)

                if msg_type == MessageType.REQUEST:
                    self.log("REQUEST", process_id, COORDINATOR_ID)
                    
                    # O Lock é usado estritamente para escrever/alterar a fila
                    with self.cs_lock:
                        self.state.enqueue_request(process_id)

                elif msg_type == MessageType.RELEASE:
                    self.log("RELEASE", process_id, COORDINATOR_ID)
                    
                    # O Lock é usado estritamente para alterar o estado da variável
                    with self.cs_lock:
                        self.is_cs_free = True

        except ConnectionResetError:
            pass
        finally:
            conn.close()

    def network_thread_func(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        print(f"Coordenador escutando em {HOST}:{PORT}")
        
        # Thread para aceitar novas conexões
        self.server_socket.settimeout(1.0)
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Erro no accept da rede: {e}")

    # Thread de algoritmo de exclusão mútua

    def algorithm_thread_func(self):
        while self.running:
            
            time.sleep(0.01) 
            
            process_id_to_grant = None
            
            # O Lock é adquirido apenas para ler e remover da fila

            with self.cs_lock:
                if self.is_cs_free and not self.state.is_queue_empty():
                    process_id_to_grant = self.state.dequeue_request()
                    if process_id_to_grant is not None:
                        self.is_cs_free = False # Ocupa a Região Crítica
            
            # O envio do GRANT ocorre FORA do Lock!
            if process_id_to_grant is not None:
                conn_info = self.state.get_connection(process_id_to_grant)
                if conn_info:
                    conn, _ = conn_info
                    try:
                        grant_msg = format_message(MessageType.GRANT, COORDINATOR_ID)
                        conn.sendall(grant_msg.encode('utf-8'))
                        self.log("GRANT", COORDINATOR_ID, process_id_to_grant)
                        self.state.increment_counter(process_id_to_grant)
                    except Exception as e:
                        print(f"Falha ao enviar GRANT para o processo {process_id_to_grant}: {e}")
                        # Caso falhe a rede, devolvemos a Região Crítica para livre
                        
                        with self.cs_lock:
                            self.is_cs_free = True

    def ui_thread_func(self):
        menu_text = "Comandos: '1' para fila, '2' para contadores, '3' para sair."
        print(f"Interface do Usuário iniciada. {menu_text}")
        while self.running:
            try:
                if sys.stdin in [None]:
                    time.sleep(0.5)
                    continue
                
                # Exibe o menu novamente
                print(f"\n{menu_text}")
                print("Escolha uma opção: ", end="", flush=True)
                cmd = input().strip()
                
                if cmd == '1':
                    queue_snapshot = self.state.get_queue_snapshot()
                    print(f"Fila de requisições atual: {queue_snapshot}")
                elif cmd == '2':
                    counters = self.state.get_counters()
                    print(f"Estatísticas de atendimento: {counters}")
                elif cmd == '3':
                    print("Encerrando o coordenador...")
                    self.running = False
                    with self.algorithm_cond:
                        self.algorithm_cond.notify_all()
                    self.server_socket.close()
                    break
                else:
                    print("Opção inválida.")
            except EOFError:
                while self.running:
                    time.sleep(1.0)
                break

    def start(self):
        self.net_thread = threading.Thread(target=self.network_thread_func, daemon=True)
        self.algo_thread = threading.Thread(target=self.algorithm_thread_func, daemon=True)
        
        self.net_thread.start()
        self.algo_thread.start()
        
        # Executa a interface do usuário na thread principal
        self.ui_thread_func()

if __name__ == "__main__":
    coord = Coordinator()
    coord.start()
