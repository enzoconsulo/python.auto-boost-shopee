#!/usr/bin/env bash
# Espera uma porta TCP aceitar conexão (usado no ExecStartPre do shopee-rodizio.service
# para não subir antes de o SOCKS do túnel estar escutando).
# Uso: scripts/esperar_porta.sh <host> <porta> [segundos, padrão 30]
set -uo pipefail
HOST="$1"
PORTA="$2"
LIMITE="${3:-30}"

for ((i = 0; i < LIMITE; i++)); do
    if (exec 3<>"/dev/tcp/$HOST/$PORTA") 2>/dev/null; then
        exit 0
    fi
    sleep 1
done
echo "$HOST:$PORTA não aceitou conexão em ${LIMITE}s" >&2
exit 1
