#!/usr/bin/env bash
# Inicia o serviço (já instalado — ver instalar_servico.sh) se estiver parado.
set -euo pipefail
sudo systemctl start shopee-rodizio
sudo systemctl status shopee-rodizio --no-pager || true
