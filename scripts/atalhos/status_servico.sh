#!/usr/bin/env bash
# Mostra se o serviço está rodando, há quanto tempo, e as últimas linhas do log do app —
# sem travar o terminal (diferente de ver_logs.sh, que segue o log ao vivo).
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
sudo systemctl status shopee-rodizio --no-pager
echo
echo "--- últimas linhas do log do app ---"
timeout 2 bash "$REPO_DIR/scripts/atalhos/ver_logs.sh" 15 2>/dev/null || true
