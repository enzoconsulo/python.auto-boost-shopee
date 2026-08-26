#!/usr/bin/env bash
# Para o serviço (fica parado até rodar iniciar_servico.sh de novo — não desabilita
# o start automático no boot; para isso, `sudo systemctl disable shopee-rodizio`).
set -euo pipefail
sudo systemctl stop shopee-rodizio
echo "serviço parado."
