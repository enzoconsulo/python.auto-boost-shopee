#!/usr/bin/env bash
# Atalho para scripts/smoke_test.py já com o config.toml do projeto. Atenção: faz UMA
# chamada real de boost (consome o limite da conta) — não rodar em automação.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$REPO_DIR"
uv run python scripts/smoke_test.py config.toml "$@"
