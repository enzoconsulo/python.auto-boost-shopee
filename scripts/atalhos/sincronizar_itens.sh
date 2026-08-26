#!/usr/bin/env bash
# Atalho para scripts/sincronizar_itens.py já com o config.toml do projeto — rode
# sempre que adicionar/remover produtos na loja. Aceita os mesmos argumentos
# extras do script (ex.: --peso-padrao N).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$REPO_DIR"
uv run python scripts/sincronizar_itens.py config.toml "$@"
