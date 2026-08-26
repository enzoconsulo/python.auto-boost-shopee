#!/usr/bin/env bash
# Mostra se o serviço está rodando, há quanto tempo, e as últimas linhas de log —
# sem travar o terminal (diferente de ver_logs.sh, que segue o log ao vivo).
sudo systemctl status shopee-rodizio --no-pager
