#!/usr/bin/env bash
# Reinicia o serviço — necessário só depois de atualizar o código (git pull). Mudança no
# config.toml NÃO precisa: ele é relido a cada ciclo. Reiniciar não queima ciclo: na
# subida o serviço espera o que falta do intervalo desde o último (ver estado.json).
set -euo pipefail
sudo systemctl restart shopee-rodizio
sudo systemctl status shopee-rodizio --no-pager || true
