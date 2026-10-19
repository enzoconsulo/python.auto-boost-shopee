#!/usr/bin/env bash
# Instala/atualiza a unidade systemd e sobe o serviço 24/7. Seguro rodar de novo
# (idempotente) depois de um `git pull` que mude systemd/shopee-rodizio.service.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DROPIN=/etc/systemd/system/shopee-rodizio.service.d/tunel.conf

sudo cp "$REPO_DIR/systemd/shopee-rodizio.service" /etc/systemd/system/

# A dependência do túnel agora está na própria unidade; o drop-in antigo que só fazia isso
# vira redundante. Só é removido se contiver exatamente as duas linhas esperadas.
if [[ -f "$DROPIN" ]] && [[ "$(grep -v '^\s*$' "$DROPIN" | sort)" == "$(printf '%s\n' 'After=shopee-proxy-tunnel.service' 'Requires=shopee-proxy-tunnel.service' '[Unit]' | sort)" ]]; then
    sudo rm "$DROPIN"
    sudo rmdir --ignore-fail-on-non-empty "$(dirname "$DROPIN")"
    echo "drop-in $DROPIN removido (redundante com a unidade do repositório)."
fi

sudo systemctl daemon-reload
sudo systemctl enable shopee-rodizio
# restart (não só start) para aplicar unidade/código novos; não queima ciclo: na subida o
# serviço espera o que falta do intervalo desde o último (ver estado.json)
sudo systemctl restart shopee-rodizio

echo "serviço instalado e rodando. Veja o log com: scripts/atalhos/ver_logs.sh"
