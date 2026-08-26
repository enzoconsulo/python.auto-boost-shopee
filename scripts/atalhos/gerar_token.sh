#!/usr/bin/env bash
# Atalho para scripts/gerar_token.py já com o config.toml do projeto — só é preciso
# rodar isso de novo se a autorização for revogada na Shopee (ver README.md).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$REPO_DIR"
uv run python scripts/gerar_token.py config.toml "$@"
