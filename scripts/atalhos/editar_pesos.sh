#!/usr/bin/env bash
# Abre o config.toml no editor e, ao sair, oferece reiniciar o serviço na hora — evita
# esquecer que ele só relê o config.toml na subida (ver __main__.py).
# Uso: scripts/atalhos/editar_pesos.sh [caminho/do/config.toml]
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG="${1:-$REPO_DIR/config.toml}"

"${EDITOR:-nano}" "$CONFIG"

read -r -p "Reiniciar o serviço agora para aplicar as mudanças? [S/n] " resposta
if [[ -z "$resposta" || "$resposta" =~ ^[Ss]$ ]]; then
    sudo systemctl restart shopee-rodizio
    echo "serviço reiniciado com o config.toml atualizado."
else
    echo "lembre de rodar scripts/atalhos/reiniciar_servico.sh depois para aplicar."
fi
