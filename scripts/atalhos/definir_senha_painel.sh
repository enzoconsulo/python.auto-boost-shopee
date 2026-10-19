#!/usr/bin/env bash
# Define/troca a senha do painel web (só o hash vai para o config.toml). Vale na hora.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$REPO_DIR"
uv run python scripts/definir_senha_painel.py config.toml "$@"
