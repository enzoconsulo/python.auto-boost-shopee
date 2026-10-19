#!/usr/bin/env bash
# Abre o config.toml no editor. Não precisa reiniciar nada: o serviço relê o config.toml
# no início de cada ciclo (ver __main__.py), então a mudança vale a partir do próximo.
# Para ajustar pesos com a lista de produtos na tela, prefira o painel web (README,
# "Painel web dos pesos").
# Uso: scripts/atalhos/editar_pesos.sh [caminho/do/config.toml]
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG="${1:-$REPO_DIR/config.toml}"

"${EDITOR:-nano}" "$CONFIG"

if PYTHONPATH="$REPO_DIR/src" "$REPO_DIR/.venv/bin/python" -c "import sys; from shopee_rodizio.config import carregar_config; carregar_config(sys.argv[1])" "$CONFIG"; then
    echo "config.toml válido — vale a partir do próximo ciclo, sem reiniciar."
else
    echo "ATENÇÃO: config.toml inválido. O serviço segue com a última versão válida até" >&2
    echo "         você corrigir o arquivo (rode este atalho de novo)." >&2
    exit 1
fi
