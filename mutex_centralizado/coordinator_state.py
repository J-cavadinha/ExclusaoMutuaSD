import threading
from collections import deque
from typing import Any, Tuple, Dict, Optional, List

class CoordinatorState:
    def __init__(self):
        # 1. Fila de Requisições
        self._request_queue = deque()
        self._queue_lock = threading.Lock()
        
        # 2. Tabela de Conexões: ID_PROCESSO -> (socket, endereço)
        self._connections: Dict[int, Tuple[Any, Any]] = {}
        self._connections_lock = threading.Lock()
        
        # 3. Contadores: ID_PROCESSO -> número de vezes atendido na região crítica
        self._counters: Dict[int, int] = {}
        self._counters_lock = threading.Lock()

    # --- Operações da Fila de Requisições ---
    def enqueue_request(self, process_id: int):
        with self._queue_lock:
            self._request_queue.append(process_id)

    def dequeue_request(self) -> Optional[int]:
        with self._queue_lock:
            if self._request_queue:
                return self._request_queue.popleft()
            return None

    def is_queue_empty(self) -> bool:
        with self._queue_lock:
            return len(self._request_queue) == 0

    def get_queue_snapshot(self) -> List[int]:
        with self._queue_lock:
            return list(self._request_queue)

    # --- Operações da Tabela de Conexões ---
    def add_connection(self, process_id: int, sock: Any, addr: Any):
        with self._connections_lock:
            self._connections[process_id] = (sock, addr)

    def remove_connection(self, process_id: int):
        with self._connections_lock:
            if process_id in self._connections:
                del self._connections[process_id]

    def get_connection(self, process_id: int) -> Optional[Tuple[Any, Any]]:
        with self._connections_lock:
            return self._connections.get(process_id)

    # --- Operações de Contadores ---
    def increment_counter(self, process_id: int):
        with self._counters_lock:
            if process_id not in self._counters:
                self._counters[process_id] = 0
            self._counters[process_id] += 1

    def get_counters(self) -> Dict[int, int]:
        with self._counters_lock:
            # Retornamos uma cópia para garantir exclusão mútua na leitura externa
            return dict(self._counters)
