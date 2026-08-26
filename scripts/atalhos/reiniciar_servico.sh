#!/usr/bin/env bash
# Reinicia o serviço — necessário depois de editar config.toml (só é lido na subida,
# ver __main__.py) ou de atualizar o código (git pull).
set -euo pipefail
sudo systemctl restart shopee-rodizio
sudo systemctl status shopee-rodizio --no-pager || true
