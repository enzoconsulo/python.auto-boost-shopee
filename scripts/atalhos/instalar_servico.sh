#!/usr/bin/env bash
# Instala/atualiza a unidade systemd e sobe o serviço 24/7. Seguro rodar de novo
# (idempotente) depois de um `git pull` que mude systemd/shopee-rodizio.service.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

sudo cp "$REPO_DIR/systemd/shopee-rodizio.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now shopee-rodizio

echo "serviço instalado e rodando. Veja o log com: scripts/atalhos/ver_logs.sh"
