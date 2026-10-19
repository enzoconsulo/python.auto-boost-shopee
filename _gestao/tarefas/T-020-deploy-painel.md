---
id: T-020
titulo: Deploy do painel — unidade systemd isolada, instalador idempotente, documentação
projeto: shopee-rodizio
status: concluida
prioridade: media
dependencias: [T-019]
areas: [systemd/shopee-painel.service, scripts/atalhos/instalar_painel.sh, scripts/atalhos/definir_senha_painel.sh, config.example.toml, README.md, CLAUDE.md, _gestao/]
tentativas: 1
agente: operacao-sbc
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
Levar o painel para o BTT Pi como serviço separado, que não derruba o rodízio e não
compete por CPU com o Klipper.

## Critérios de aceite
- [x] `systemd/shopee-painel.service` no padrão das outras duas (biqu,
      `/home/biqu/shopee-rodizio`), sem `Requires`/`After` do rodízio nem do túnel;
      `Nice=19`, `CPUSchedulingPolicy=idle`, `IOSchedulingClass=idle`, `CPUQuota=50%`,
      `MemoryMax=96M`, `SuccessExitStatus=143`, `ProtectSystem=strict` com escrita só na
      pasta do projeto.
- [x] `scripts/atalhos/instalar_painel.sh` idempotente: `uv sync`, confere se a porta está
      livre (ou é do próprio painel), pede a senha se ainda não houver hash, instala a
      unidade e reinicia; imprime a URL da LAN.
- [x] README ("Painel web dos pesos"): porta 8790 justificada contra as ocupadas no Pi
      (conferido com `ss -ltn` em 2026-10-19), escopo só-LAN, defesas, aplicação sem
      restart, cache, isolamento de CPU, aviso sobre `sincronizar_itens.sh`.
- [x] `config.example.toml` com a seção `[painel]` comentada.
- [x] CLAUDE.md, GUIA.md, MAPA.md, DECISOES.md e PROGRESSO.md atualizados.
- [x] Instalado e verificado no Pi real (ver PROGRESSO 2026-10-19).
