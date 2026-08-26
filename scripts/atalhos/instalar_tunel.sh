#!/usr/bin/env bash
# Instala/atualiza o túnel SSH que fixa o IP de saída das chamadas à Shopee (ver README,
# "IP de saída fixo"). Edite systemd/shopee-proxy-tunnel.service com o IP da sua VM Oracle
# ANTES de rodar isto. Idempotente — seguro rodar de novo após mudar a unidade.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIDADE="$REPO_DIR/systemd/shopee-proxy-tunnel.service"

if grep -q '<IP-DA-VM-ORACLE>' "$UNIDADE"; then
    echo "erro: edite $UNIDADE e troque <IP-DA-VM-ORACLE> pelo IP público da sua VM" >&2
    echo "      antes de instalar o túnel (ver README, 'IP de saída fixo')." >&2
    exit 1
fi

sudo cp "$UNIDADE" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now shopee-proxy-tunnel

echo "túnel instalado e rodando. Veja o status com: scripts/atalhos/status_tunel.sh"
