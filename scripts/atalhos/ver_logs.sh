#!/usr/bin/env bash
# Segue o log ao vivo. Ctrl+C só fecha esta visualização — o serviço continua rodando
# em segundo plano (ele é gerenciado pelo systemd, não por este terminal).
# Uso: scripts/atalhos/ver_logs.sh [linhas-de-historico-antes-de-seguir]
journalctl -u shopee-rodizio -f -n "${1:-50}"
