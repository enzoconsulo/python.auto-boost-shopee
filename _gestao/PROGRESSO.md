# Progresso — shopee-rodizio

Diário do projeto, entradas mais recentes NO TOPO. Formato:

## AAAA-MM-DD
<o que avançou, estado atual, próximos passos visíveis — 3–6 linhas>

## 2026-10-19

Auditoria de produção corrigida e painel web entregue (T-012 a T-020):
- restart não queima mais ciclo (espera o restante do intervalo pelo `estado.json`);
- `config.toml` é relido a cada ciclo;
- escrita do config é atômica e durável e troca só os `[[itens]]` (o regenerador antigo
  apagaria o `[rede]` de produção, que fica depois dos itens);
- unidade systemd depende do túnel, com espera da porta SOCKS e `SuccessExitStatus=143`;
- `ver_logs.sh` segue o log do app;
- mensagens de erro sem `access_token` (havia 5 vazados no log do Pi);
- catálogo extraído para `catalogo.py`, com cache;
- painel web só-LAN na porta 8790 (`shopee-painel.service`, prioridade idle).

Implantado no BTT Pi via `git pull`, com o drop-in `tunel.conf` removido. Próximo passo:
o usuário define a senha do painel (`scripts/atalhos/definir_senha_painel.sh`), se ainda
não o fez no deploy, e valida no navegador a extração de preço/estoque (DECISOES
2026-10-19).

## 2026-08-25

Todas as 11 tarefas do backlog (T-001 a T-011) concluídas: scaffold, config TOML validada,
estado/histórico em JSON com escrita atômica, cliente HTTP da Shopee (assinatura HMAC,
renovação automática de token), boost de item, seleção ponderada sem reposição, logging
com rotação, orquestração do ciclo + loop principal (com persistência do token renovado,
RF-02), unidade systemd para deploy no BTT Pi, script de smoke-test manual contra a API
real, e correção de lint. Suíte com 55 testes passando, `ruff check .` limpo. Serviço
funcionalmente completo; falta apenas confirmar o `endpoint_boost` com credenciais reais
no primeiro deploy (ver seção correspondente do README e `_gestao/DECISOES.md`). Próximo
passo: deploy real no BTT Pi.

## 2026-08-24
Projeto criado pelo orquestrador via /novo-projeto. Estrutura inicial (`_gestao/`,
CLAUDE.md, README.md) montada; repositório git próprio inicializado. Próximo passo:
planejador produz ESPECIFICACAO.md, PLANO.md, equipe.json e o backlog de tarefas.
