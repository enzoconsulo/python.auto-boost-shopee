#!/usr/bin/env bash
# Segue ao vivo o log do APP — o arquivo de [caminhos].log do config.toml, onde o serviço
# escreve cada boost, espera e erro (o logging do app vai para arquivo, não para o stdout,
# por isso o journal sozinho não mostra isso).
#
# Com -j, segue o journal do systemd: start/stop/restart, crash antes do logging subir,
# e o log do painel web. Os dois têm informação diferente e complementar.
#
# Ctrl+C só fecha esta visualização — o serviço continua rodando em segundo plano.
# Uso: scripts/atalhos/ver_logs.sh [-j] [linhas-de-historico-antes-de-seguir]
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG="${CONFIG:-$REPO_DIR/config.toml}"

if [[ "${1:-}" == "-j" || "${1:-}" == "--journal" ]]; then
    shift
    exec journalctl -u shopee-rodizio -u shopee-painel -u shopee-proxy-tunnel -f -n "${1:-50}"
fi

PYTHON="$REPO_DIR/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON=python3

# caminho relativo é relativo ao WorkingDirectory do serviço, que é a raiz do projeto
LOG="$("$PYTHON" - "$CONFIG" "$REPO_DIR" <<'PY'
import pathlib
import sys
import tomllib

with open(sys.argv[1], "rb") as handle:
    caminho = pathlib.Path(tomllib.load(handle)["caminhos"]["log"])
print(caminho if caminho.is_absolute() else pathlib.Path(sys.argv[2]) / caminho)
PY
)"

echo "seguindo $LOG (use -j para o journal do systemd)"
exec tail -n "${1:-50}" -F "$LOG"
