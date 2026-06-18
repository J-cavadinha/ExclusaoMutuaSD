from enum import Enum

MESSAGE_SIZE = 16

class MessageType(Enum):
    REQUEST = 1
    GRANT = 2
    RELEASE = 3

def format_message(msg_type: MessageType, process_id: int) -> str:
    ##Formata a mensagem para um tamanho fixo.
    base_msg = f"{msg_type.value}|{process_id}|"
    if len(base_msg) > MESSAGE_SIZE:
        raise ValueError("O conteúdo da mensagem excede o tamanho fixo máximo.")
    
    padding_length = MESSAGE_SIZE - len(base_msg)
    padding = "0" * padding_length
    
    return base_msg + padding

def parse_message(message: str) -> tuple[MessageType, int]:
    #Decodifica a mensagem em formato string, retornando o tipo e o ID do processo.
    if len(message) != MESSAGE_SIZE:
        raise ValueError(f"Tamanho de mensagem inválido. Esperado {MESSAGE_SIZE}, obtido {len(message)}")
    
    parts = message.split("|")
    if len(parts) < 2:
        raise ValueError("Formato de mensagem inválido.")
    
    try:
        msg_type = MessageType(int(parts[0]))
        process_id = int(parts[1])
    except ValueError as e:
        raise ValueError(f"Falha ao decodificar partes da mensagem: {e}")
        
    return msg_type, process_id
