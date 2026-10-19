#!/usr/bin/env bash
# Instala/atualiza o painel web dos pesos (systemd/shopee-painel.service) e sobe. Seguro
# rodar de novo (idempotente) depois de um `git pull`. Ver README, "Painel web dos pesos".
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG="$REPO_DIR/config.toml"

cd "$REPO_DIR"
# o painel roda o python do .venv direto: garante o pacote e as dependências instalados
uv sync --quiet

PORTA="$(PYTHONPATH="$REPO_DIR/src" .venv/bin/python -c \
    'import sys; from shopee_rodizio.config import carregar_config; print(carregar_config(sys.argv[1]).painel.porta)' \
    "$CONFIG")"

# porta ocupada por outro programa (não por uma versão anterior do próprio painel)?
if ss -ltnpH "sport = :$PORTA" 2>/dev/null | grep -q . \
    && ! systemctl is-active --quiet shopee-painel; then
    echo "erro: a porta $PORTA já está em uso por outro programa:" >&2
    ss -ltnp "sport = :$PORTA" >&2 || true
    echo "      escolha outra em [painel].porta do config.toml." >&2
    exit 1
fi

if ! grep -Eq '^\s*senha_hash\s*=' "$CONFIG"; then
    echo "senha do painel ainda não definida — defina agora:"
    uv run python scripts/definir_senha_painel.py "$CONFIG"
fi

sudo cp "$REPO_DIR/systemd/shopee-painel.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shopee-painel
sudo systemctl restart shopee-painel

IP="$(hostname -I | awk '{print $1}')"
echo "painel rodando: abra http://$IP:$PORTA num computador da sua rede local."
echo "log do painel: scripts/atalhos/ver_logs.sh -j"
