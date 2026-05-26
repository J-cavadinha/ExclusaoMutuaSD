#!/bin/bash

# Valores padrão caso não sejam passados
N=${1:-3}
R=${2:-2}
K=${3:-1}

echo "=================================================="
echo " Iniciando Teste de Exclusão Mútua Centralizada"
echo " Processos (N): $N | Repetições (R): $R | Espera (K): $K seg"
echo "=================================================="

echo "[1] Limpando arquivos antigos..."
rm -f coordinator.log resultado.txt

echo "[2] Iniciando Coordenador em background..."
# O uso de 'python -u' desativa o buffer de saída do Python, 
# garantindo que os prints vão imediatamente para o log.
python -u coordinator.py > coordinator.log 2>&1 &
COORD_PID=$!

# Aguarda 1 segundo para garantir que o socket do coordenador esteja online
sleep 1

echo "[3] Iniciando $N processos simultaneamente..."
PIDS=""
for i in $(seq 1 $N); do
    python -u process.py $i $R $K > /dev/null 2>&1 &
    PIDS="$PIDS $!"
done

echo "[4] Aguardando a execução dos processos..."
# Aguarda especificamente as instâncias dos processos clientes terminarem
wait $PIDS

echo "[5] Processos finalizados. Encerrando o coordenador..."
kill -SIGTERM $COORD_PID
sleep 1

echo "=================================================="
echo " Execução concluída. Arquivos gerados:"
echo " - resultado.txt"
echo " - coordinator.log"
echo "=================================================="
