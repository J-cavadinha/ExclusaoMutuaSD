import sys
from datetime import datetime

def validate(n: int, r: int):
    print(f"Validando resultados para N={n} processos, R={r} repetições...")
    
    # 1. Validar resultado.txt
    try:
        with open("resultado.txt", "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("FALHA: O arquivo 'resultado.txt' não foi encontrado.")
        return False

    # a) Exatamente N * R linhas
    expected_lines = n * r
    if len(lines) != expected_lines:
        print(f"FALHA [a]: 'resultado.txt' possui {len(lines)} linhas. Era esperado exatamente {expected_lines} (N*R).")
        return False
    else:
        print("OK: 'resultado.txt' possui a quantidade correta de linhas.")

    # b) Timestamps em ordem estritamente cronológica
    previous_time = None
    for idx, line in enumerate(lines):
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            print(f"FALHA: Linha mal formatada em 'resultado.txt' na linha {idx+1}")
            return False
        
        timestamp_str = parts[1]
        try:
            current_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            print(f"FALHA: Erro no parse do timestamp '{timestamp_str}' na linha {idx+1}")
            return False
        
        if previous_time is not None:
            if current_time < previous_time:
                print(f"FALHA [b]: Quebra da ordem cronológica na linha {idx+1}. {current_time} veio antes de {previous_time}.")
                return False
        previous_time = current_time
    
    print("OK: Timestamps em 'resultado.txt' estão em ordem estritamente cronológica.")

    # 2. Validar coordinator.log
    # c) Todo GRANT é seguido de um RELEASE do mesmo processo antes que outro GRANT seja emitido.
    try:
        with open("coordinator.log", "r", encoding="utf-8", errors="replace") as f:
            log_lines = f.readlines()
    except FileNotFoundError:
        print("FALHA: O arquivo 'coordinator.log' não foi encontrado.")
        return False

    current_granted_process = None
    grant_count = 0
    release_count = 0
    request_sequence = []
    release_sequence = []
    
    for line in log_lines:
        if " - " not in line:
            continue
            
        parts = line.strip().split(" - ")
        if len(parts) < 3:
            continue
            
        msg_type_str = parts[1].replace("[", "").replace("]", "")
        routing_str = parts[2] # Exemplo: "[0] -> [1]" ou "[1] -> [0]"
        
        if msg_type_str == "REQUEST":
            src = int(routing_str.split("->")[0].replace("[", "").replace("]", "").strip())
            request_sequence.append(src)
            
        elif msg_type_str == "GRANT":
            grant_count += 1
            if current_granted_process is not None:
                print(f"FALHA [c]: VIOLAÇÃO DE EXCLUSÃO MÚTUA! Processo {current_granted_process} estava na Região Crítica quando um novo GRANT foi emitido.")
                return False
            
            # Extrai o ID do processo de destino
            dest = int(routing_str.split("->")[1].replace("[", "").replace("]", "").strip())
            current_granted_process = dest
            
        elif msg_type_str == "RELEASE":
            release_count += 1
            # Extrai o ID do processo de origem
            src = int(routing_str.split("->")[0].replace("[", "").replace("]", "").strip())
            release_sequence.append(src)
            
            # Verifica se o RELEASE veio de quem realmente tinha o GRANT
            if current_granted_process == src:
                current_granted_process = None
                
    if grant_count != expected_lines:
        print(f"FALHA: Houve um número incorreto de GRANTs no log. Esperado {expected_lines}, encontrado {grant_count}.")
        return False

    if request_sequence != release_sequence:
        print(f"FALHA: A ordem dos REQUESTs {request_sequence} não condiz com a ordem dos RELEASEs {release_sequence}.")
        return False
    else:
        print("OK: A ordem das mensagens REQUEST é idêntica à ordem das mensagens RELEASE (Fila FIFO garantida).")
        
    print(f"OK: Encontrados {grant_count} GRANTs e {release_count} RELEASEs consistentes no 'coordinator.log'. Nenhuma violação de exclusão mútua!")
    print("\n>>> SUCESSO: O ALGORITMO FUNCIONA CORRETAMENTE! <<<")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python validator.py <N_PROCESSOS> <R_REPETICOES>")
        sys.exit(1)
        
    n = int(sys.argv[1])
    r = int(sys.argv[2])
    
    success = validate(n, r)
    sys.exit(0 if success else 1)
