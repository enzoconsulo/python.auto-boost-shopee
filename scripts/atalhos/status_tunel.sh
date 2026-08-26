#!/usr/bin/env bash
# Mostra se o túnel SSH (IP de saída fixo pra Shopee) está de pé — sem travar o terminal.
sudo systemctl status shopee-proxy-tunnel --no-pager
