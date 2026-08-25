---
id: T-008
titulo: Orquestração do ciclo de rodízio e loop de agendamento
projeto: shopee-rodizio
status: em-teste
prioridade: alta
dependencias: [T-003, T-005, T-006, T-007]
areas: [src/shopee_rodizio/ciclo.py, src/shopee_rodizio/__main__.py, tests/test_ciclo.py]
tentativas: 3
agente: operacao-sbc
criada: 2026-08-24
atualizada: 2026-08-25
ultima-reprovacao: revisor
---

## Objetivo
Implementar `src/shopee_rodizio/ciclo.py` (um ciclo completo: seleciona itens via
`selecao.py`, impulsiona cada um via `boost.py`, grava resultado via `estado.py`, loga via
`logging_config.py`) e `src/shopee_rodizio/__main__.py` (entrypoint: carrega config, loga,
entra no loop `time.sleep(intervalo_horas * 3600)` chamando um ciclo a cada volta). Este é
o módulo que junta tudo — ao final desta tarefa, `uv run python -m shopee_rodizio` executa
o rodízio de verdade contra a API real (dado um `config.toml` válido do usuário).

## Contexto
Invariante mais importante do projeto inteiro (RF-06): **nenhum erro dentro de um ciclo
pode terminar o processo.** Erro de rede, de API, de token — tudo isso já deveria voltar
como resultado estruturado de `cliente_shopee.py`/`boost.py` (T-004/T-005); aqui, mesmo
assim, envolva a execução de cada ciclo num `try/except Exception` amplo que loga e segue
para o próximo ciclo, como última rede de segurança (defesa em profundidade — um bug
futuro em qualquer módulo não deve conseguir derrubar o serviço 24/7).

`__main__.py` deve aceitar o caminho do arquivo de config como argumento (ex.:
`uv run python -m shopee_rodizio caminho/para/config.toml`, com um padrão razoável tipo
`config.toml` no diretório atual se omitido).

Nos testes, mocke `boost.impulsionar` e `time.sleep` (não espere 4h de verdade nem chame a
API real) — teste o CONTEÚDO de um ciclo (`ciclo.py`) diretamente, sem depender do loop
infinito de `__main__.py`; para o loop em si, um teste com `time.sleep` mockado e um limite
de iterações (ex.: parar depois de 2 voltas) é suficiente para provar que ele não quebra.

## Critérios de aceite
- [x] `uv run pytest tests/test_ciclo.py -q` → todos os testes passam, incluindo: ciclo com
      todos os boosts com sucesso, ciclo com pelo menos um boost falhando (rede ou API) sem
      que a exceção escape, e o histórico (estado) é gravado ao final do ciclo em ambos os
      casos.
      `verificar: uv run pytest tests/test_ciclo.py -q`
- [x] `uv run python -m shopee_rodizio --help` (ou equivalente) não lança traceback — mostra
      uso esperado do comando.
      `verificar: uv run python -m shopee_rodizio --help`
- [x] `uv run ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py` → sem
      erros.
      `verificar: uv run ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py`

## Notas de execução

### Ciclo 1

**Implementado:**
- `src/shopee_rodizio/ciclo.py` — `executar_ciclo(cliente, config, estado) -> Estado`:
  seleciona itens via `selecao.selecionar`, chama `boost.impulsionar` (módulo importado, não
  a função diretamente — necessário para o `patch.object(boost, "impulsionar", ...)` dos
  testes funcionar) para cada um, grava cada resultado via `estado.registrar_boost` (que já
  persiste em disco atomicamente) e loga (INFO em sucesso, WARNING em falha). Cada item é
  envolvido num `try/except Exception` — defesa em profundidade (RF-06): mesmo
  `boost.impulsionar` já não devendo lançar, um bug futuro em qualquer módulo abaixo vira
  falha registrada no histórico, não uma exceção que propaga.
- `src/shopee_rodizio/__main__.py` — `executar_loop(caminho_config, *, max_iteracoes=None)`:
  carrega config, configura logging, cria `ClienteShopee` a partir da config (token
  `expira_em=None`, então o cliente renova o `access_token` sozinho na primeira chamada) e
  carrega o `Estado`. Loop `while max_iteracoes is None or iteracao < max_iteracoes`: chama
  `executar_ciclo` dentro de outro `try/except Exception` (segunda camada de defesa, cobrindo
  também `selecao`/`estado`, não só `boost`), loga erro inesperado com `logger.exception` e
  segue; depois dorme `config.ciclo.intervalo_horas * 3600`. `max_iteracoes` existe só para
  teste (evita loop infinito/`sleep` real de 4h); em produção fica `None` e o loop não para.
  `main()` usa `argparse` com um argumento posicional opcional `config` (padrão
  `config.toml`) — `--help`/`-h` é tratado pelo próprio `argparse`, que sai com código 0
  antes de qualquer tentativa de carregar config (por isso `--help` funciona mesmo sem
  `config.toml` no diretório).
- `tests/test_ciclo.py` — 7 casos: sucesso em todos os itens; um boost falhando por erro de
  API (retorno `ResultadoBoost(sucesso=False, ...)`, sem lançar) sem que os demais itens
  sejam afetados; um boost lançando exceção inesperada (`ConnectionError`) sem que ela escape
  de `executar_ciclo`; respeito ao `limite_slots`; ciclo sem itens não grava nada; loop
  principal roda um número limitado de iterações sem travar (com `time.sleep` mockado); loop
  principal segue rodando mesmo quando `executar_ciclo` lança (RF-06 na camada do loop).

**Decisão de teste:** `ciclo.py` importa `from . import boost` (módulo) em vez de
`from .boost import impulsionar` — só assim `patch.object(boost, "impulsionar", ...)` nos
testes intercepta a chamada; com import direto da função o patch não teria efeito (o nome já
estaria vinculado no namespace de `ciclo.py` antes do patch).

**Achado corrigido no caminho:** a fixture `_config_arquivo` inicialmente usava caminhos
relativos (`log = "shopee-rodizio.log"`, `estado = "estado.json"`) no TOML de teste — como o
`pytest` roda com cwd na raiz do projeto, os dois testes do loop principal estavam gravando
`estado.json` e `shopee-rodizio.log` de verdade na raiz do repositório a cada execução da
suíte. Corrigido para usar caminhos absolutos dentro de `tmp_path`; os dois arquivos vazados
foram apagados antes do commit (não fazem parte da entrega).

**Verificação manual (fora do pytest):** rodei `executar_loop` com config real (TOML de
tempdir), `boost.impulsionar` mockado e `time.sleep` mockado por 2 iterações — confirmei que
`estado.json` e o arquivo de log são gravados corretamente com os dois registros esperados
(ver saída no relatório final).

**Reproduzir:**
`.venv\Scripts\python.exe -m pytest tests/test_ciclo.py -q`
`.venv\Scripts\python.exe -m shopee_rodizio --help`
`.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py`

**Nota sobre o comando dos critérios:** `uv` não está no PATH desta máquina; os comandos
acima com `.venv\Scripts\python.exe -m ...` são equivalentes e foram os efetivamente
executados (ver memória de projeto sobre isso, já registrada em ciclos anteriores).

**Commit:** `5197e89`

### Ciclo 2 (retrabalho — executor reforçado)

**Causa raiz da reprovação (revisor, crítica):** a tarefa passava nos 3 critérios de aceite,
mas descumpria o RF-02 ("persistindo o token renovado"). O token renovado (`cliente.token`,
mutado in-place por `ClienteShopee._aplicar_renovacao`) nunca era lido nem gravado em disco
pelo módulo orquestrador. Num restart do systemd (`Restart=on-failure`, RF-08), `_cliente_de`
reconstruía o cliente com o `refresh_token` velho do `config.toml` — possivelmente já
invalidado pela renovação anterior — quebrando a autenticação permanentemente. T-004/T-005
já haviam registrado que essa persistência era responsabilidade da T-008.

**Aproveitamento:** ~90% do ciclo anterior mantido. `ciclo.py` **não foi tocado** (a
persistência é responsabilidade do loop, não de um ciclo isolado). A correção foi cirúrgica
em `__main__.py` + testes — não houve refação de abordagem, só o fechamento da lacuna que o
revisor apontou.

**Implementado (só o que reprovou):**
- `src/shopee_rodizio/__main__.py`:
  - `_caminho_token(config)` — deriva `token.json` como irmão do `estado.json` (é estado de
    runtime, não config do usuário; por isso não reescrevo o `config.toml`, que é editável à
    mão e perderia comentários/formatação, e fica fora das `areas` da tarefa).
  - `_carregar_token(caminho) -> Token | None` / `_persistir_token(caminho, token)` — leitura
    e escrita atômica (tmp + `os.replace`, mesmo idioma do `estado.py`), com `expira_em`
    serializado via `isoformat`/`fromisoformat`.
  - `_cliente_de(config, token=None)` — passa a aceitar um token persistido; quando presente,
    o cliente é reconstruído com ele (access/refresh/expira_em) em vez do token do
    `config.toml`. É o que torna o restart seguro.
  - `executar_loop` — na subida, carrega o token persistido (`token_anterior`); após cada
    ciclo, se `cliente.token != token_anterior`, grava o novo e atualiza a referência. Só
    escreve quando há renovação de fato (frozen dataclass compara por valor) — sem I/O
    desnecessário nos ciclos sem renovação.
- `tests/test_ciclo.py` — 6 casos novos: round-trip `_persistir_token`/`_carregar_token`;
  token inexistente devolve `None`; `_cliente_de` usa o token persistido no lugar do config
  (prova de restart); `_cliente_de` sem token persistido cai no config; loop grava
  `token.json` quando o ciclo renova o token; loop **não** grava quando não há renovação.

**Nota (segredo em disco):** `token.json` guarda `access_token`/`refresh_token` em texto —
mesma exposição já existente no `config.toml` e no diretório de estado; nenhuma superfície
nova. Fica no mesmo diretório protegido do usuário no BTT Pi.

**Reproduzir:**
`.venv\Scripts\python.exe -m pytest tests/test_ciclo.py -q` → 13 passed
`.venv\Scripts\python.exe -m pytest -q` → 53 passed (era 47; +6 testes novos, sem regressão)
`.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py` → All checks passed!
`.venv\Scripts\python.exe -m shopee_rodizio --help` → mostra uso, sem traceback

### Ciclo 3 (retrabalho — executor reforçado)

**Causa raiz da reprovação (revisor, crítica):** o trabalho do Ciclo 2 (persistência do
token, RF-02) existia só na árvore de trabalho — **nunca foi commitado**. `git log` de
`__main__.py` mostrava um único commit (`5197e89`, do Ciclo 1); o conteúdo aprovado na
Verificação vivia como `M` no working tree, perdível por qualquer `git reset`/`checkout`. Foi
uma falha de PROCESSO (commit ausente), não de implementação — o código estava correto.

**Aproveitamento:** ~95% mantido. O conteúdo do Ciclo 2 estava íntegro no working tree (13
testes passando ao subir) e foi preservado por inteiro. Não refiz abordagem nenhuma; além de
commitar o que faltava, fechei os outros dois achados do revisor, ambos dentro das `areas` e
apontados por ele (não é escopo novo).

**Implementado (só o que o revisor apontou):**
- **[crítica] commit ausente** → este ciclo commita o conteúdo do Ciclo 2 + os dois reparos
  abaixo num único commit (hash ao fim), fechando a lacuna de processo.
- **[importante] `ciclo.py`** — `registrar_boost` agora roda dentro de um `try/except` próprio
  (antes ficava fora do `try` que envolvia só `boost.impulsionar`). Uma falha de I/O ao gravar
  o histórico não escapa mais de `executar_ciclo` (que documenta "Nunca lança"); assim, se um
  item já renovou o token in-place, o loop de `__main__.py` sempre alcança o bloco de
  persistência do token novo (RF-02) — o gap que o revisor descreveu fica fechado na origem.
  Novo teste `test_ciclo_com_falha_ao_gravar_historico_nao_escapa`.
- **[menor] `__main__.py`** — `token_anterior` passa a ser inicializado com `cliente.token`
  (o token com que o cliente REALMENTE subiu), não com o retorno cru de `_carregar_token`. Na
  primeira subida sem `token.json`, isso evita a gravação redundante ao fim do 1º ciclo: só
  grava quando há renovação de fato. Novo teste
  `test_loop_primeira_subida_sem_renovacao_nao_grava_token_com_cliente_real` (usa o
  `_cliente_de` REAL, cobrindo o caso que o teste mockado não pegava, como o revisor notou).

**Reproduzir:**
`.venv\Scripts\python.exe -m pytest tests/test_ciclo.py -q` → 15 passed (era 13; +2 novos)
`.venv\Scripts\python.exe -m pytest -q` → 55 passed (era 53; sem regressão)
`.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py` → All checks passed!
`.venv\Scripts\python.exe -m shopee_rodizio --help` → mostra uso, sem traceback

**Commit:** `21df47f`

## Verificação

### Ciclo 3 (testador)

- **[PASSOU] [executado] Critério 1: todos os testes de `test_ciclo.py` passam, incluindo a persistência do token**
  Comando: `.venv\Scripts\python.exe -m pytest tests/test_ciclo.py -q`
  Saída: `13 passed in 0.48s` — inclui os 7 testes originais + 6 testes novos do ciclo 2 que verificam:
    - `test_persistir_e_carregar_token_faz_roundtrip` — round-trip do arquivo de token
    - `test_carregar_token_inexistente_devolve_none` — carregamento seguro
    - `test_cliente_de_usa_token_persistido_em_vez_do_config_apos_restart` — restart seguro (Token antigo será descartado)
    - `test_cliente_de_sem_token_persistido_usa_config` — fallback para config se sem persistência
    - `test_loop_persiste_token_renovado_apos_ciclo` — gravação de token renovado
    - `test_loop_nao_grava_token_quando_nao_ha_renovacao` — evita I/O desnecessário

- **[PASSOU] [executado] Critério 2: `--help` não lança traceback e mostra uso esperado**
  Comando: `.venv\Scripts\python.exe -m shopee_rodizio --help`
  Saída: mostra `usage: python -m shopee_rodizio [-h] [config]`, descrição e argumentos, sem erro.

- **[PASSOU] [executado] Critério 3: `ruff check` dos dois arquivos passou**
  Comando: `.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py`
  Saída: `All checks passed!`

Suíte completa: 53 passed — `.venv\Scripts\python.exe -m pytest -q`
Mutação: `_persistir_token` desabilitado → testes `test_persistir_e_carregar_token_faz_roundtrip` e `test_loop_persiste_token_renovado_apos_ciclo` FALHAM (esperado) — prova que os testes novos realmente detectam a implementação
Graus de prova: 4 executados, 0 inspecionados, 0 julgados

## Conformidade

### Ciclo 1

Conformidade: cumpre-parcial

- `uv run pytest tests/test_ciclo.py -q` (7 casos: sucesso, falha de API, exceção
  inesperada, limite de slots, ciclo vazio, loop com iterações limitadas, loop resiliente a
  exceção) → `src/shopee_rodizio/ciclo.py:20-39`, `src/shopee_rodizio/__main__.py:38-65`,
  `tests/test_ciclo.py`. Reexecutei: 7 passed.
- `python -m shopee_rodizio --help` não lança traceback → `_analisar_args`
  (`__main__.py:22-33`), delegado ao `argparse`. Reexecutei: mostra uso, sai limpo.
- `ruff check ciclo.py __main__.py` sem erros → reexecutei: All checks passed!.
- Objetivo ("`ciclo.py` seleciona, impulsiona, grava, loga"; "`__main__.py` carrega config,
  loga, entra no loop `time.sleep(intervalo_horas * 3600)`") → cumprido literalmente:
  `executar_ciclo` (`ciclo.py:20`) e `executar_loop` (`__main__.py:38`).
- RF-06 (nenhum erro derruba o processo) → duas camadas de `try/except Exception`
  (`ciclo.py:29-35` por item, `__main__.py:58-59` por ciclo), cobertas por
  `test_ciclo_com_excecao_inesperada_de_rede_nao_escapa_e_grava_falha` e
  `test_loop_principal_continua_apos_ciclo_lancar_excecao_inesperada`.
- **O que falta:** RF-02 ("renova o `access_token`... persistindo o token renovado") não é
  atendido por este módulo — ver achado `crítica` na Revisão. Isto é parte do Objetivo, não
  acessório: T-004 e T-005 já registraram explicitamente que essa persistência ficaria a
  cargo de T-008 (única peça que tem, ao mesmo tempo, o `cliente` e um lugar para gravar em
  disco), e RF-08 (systemd `Restart=on-failure`, T-009) garante que o processo reinicia em
  produção — sem a persistência, o "rodízio de verdade contra a API real" que o Objetivo
  promete quebra depois do primeiro restart seguinte a uma renovação de token.
- Escopo: tocou exatamente as `areas` declaradas (`ciclo.py`, `__main__.py`,
  `tests/test_ciclo.py`); sem sobra.

### Ciclo 2

Conformidade: cumpre

O gap de RF-02 apontado no Ciclo 1 (token renovado nunca lido/persistido) está fechado
**no conteúdo**:
- `_caminho_token`, `_carregar_token`, `_persistir_token` (`__main__.py`, novo) — leitura e
  escrita atômica (tmp + `os.replace`) de `token.json`, irmão do `estado.json`.
- `_cliente_de(config, token=None)` passa a aceitar o token persistido e reconstrói o
  cliente com ele quando presente, em vez do `refresh_token` (potencialmente já invalidado)
  do `config.toml` — é exatamente o restart seguro que faltava.
- `executar_loop` carrega o token na subida, e após cada ciclo persiste `cliente.token`
  quando ele mudou (`!= token_anterior`) — evita I/O redundante nos ciclos sem renovação.
- Cobertura nova em `tests/test_ciclo.py`: round-trip de `_persistir_token`/`_carregar_token`,
  `_cliente_de` usando token persistido vs. fallback para config, loop persistindo token
  renovado e loop **não** persistindo quando não há renovação. Reexecutei:
  `pytest tests/test_ciclo.py -q` → 13 passed; `ruff check ciclo.py __main__.py` → All
  checks passed — bate com o que a Verificação (Ciclo 3, testador) registrou.
- Escopo: só `__main__.py` e `tests/test_ciclo.py` foram tocados nesta rodada — `ciclo.py`
  permanece igual ao Ciclo 1, como as Notas afirmam; confirmado por `git diff`.

**Mas o critério de entrega não está cumprido**, ver achado `crítica` na Revisão: este
conteúdo, correto, nunca chegou a um commit. `Conformidade: cumpre` refere-se estritamente
ao que o código faz; o veredito do ciclo (abaixo) é reprovação, motivada só por esse achado
de processo — não peço reabrir a implementação.

## Revisão

### Ciclo 2

- **[crítica] processo — o trabalho deste ciclo nunca foi commitado.** `git log --oneline
  -- src/shopee_rodizio/__main__.py` mostra um único commit tocando o arquivo (`5197e89`,
  o do Ciclo 1); `git status` mostra `src/shopee_rodizio/__main__.py` e `tests/test_ciclo.py`
  como `M` (modificados, não commitados) na árvore de trabalho — é ali, e só ali, que existe
  a persistência de token descrita nas Notas do Ciclo 2 e aprovada na Verificação do Ciclo 3
  (testador). As Notas de execução não têm uma segunda linha `**Commit:**` para este ciclo
  (só a do Ciclo 1, `5197e89`), e não há commit nenhum no histórico com essas mudanças para
  registrar — não é caso de "hash esquecido de anotar" (o fallback do meu protocolo,
  `git log --grep`), é ausência real do commit.
  **Cenário de falha concreto:** o pipeline desta fábrica usa `git show <hash>` como fonte
  de verdade de toda revisão e auditoria; um `status: concluida` aqui declarara "entregue"
  um estado que só existe na árvore de trabalho local — perdível por qualquer `git checkout`,
  `git reset`, ou por outro agente/tarefa que rode em paralelo e mexa na árvore, sem deixar
  rastro nenhum em `git log`. Isso já aconteceu de fato num ciclo anterior de outro projeto
  desta fábrica (arquivo vazado/perdido por falta de disciplina de commit); aqui o risco é
  maior porque é o próprio RF-02 — a garantia de não perder credencial — que ficaria não
  commitada.
  **Correção esperada, cirúrgica:** o conteúdo já está correto e testado (ver Conformidade);
  não é para refazer a implementação, é para commitar exatamente o que já está na árvore de
  trabalho (`git add src/shopee_rodizio/__main__.py tests/test_ciclo.py && git commit`) e
  registrar o novo hash numa linha `**Commit:**` nas Notas do Ciclo 2.
- **[importante]** `src/shopee_rodizio/ciclo.py:36` — `registrar_boost` roda FORA do
  `try/except` que envolve só `boost.impulsionar` (linhas 29-34); se ele lançar (ex.: falha
  de I/O ao gravar `estado.json` — SD card de SBC 24/7 é hardware plausivelmente instável) na
  mesma volta em que `boost.impulsionar` já renovou o token, a exceção escapa de
  `executar_ciclo` até o `except Exception` de `__main__.py:113-119`, que fica ANTES do bloco
  `if cliente.token != token_anterior: _persistir_token(...)` — o token recém-renovado (com
  `refresh_token` novo, possivelmente já tendo invalidado o antigo do lado da Shopee) não é
  persistido nesta volta. Se o processo reiniciar antes da próxima renovação bem-sucedida
  (~4h de intervalo padrão), o restart usa o `refresh_token` velho e reproduz exatamente a
  falha de autenticação permanente que este ciclo foi criado para fechar. Não bloqueia a
  aprovação sozinho (não é crítica: exige uma falha de I/O bem cronometrada, não é o caminho
  normal), mas é uma lacuna real na garantia que RF-02 promete — mover a chamada de
  `registrar_boost` para dentro do mesmo `try` (ou mover a checagem/persistência do token
  para antes do `registrar_boost`, dentro de `ciclo.py`) fecha o gap.
- **[menor]** `__main__.py:_cliente_de` com `token=None` sempre constrói
  `Token(..., expira_em=None)`; na primeiríssima subida (sem `token.json` ainda),
  `cliente.token` já nasce diferente de `token_anterior=None`, então o loop grava
  `token.json` no fim do primeiro ciclo mesmo que nenhuma renovação real tenha ocorrido
  (ex.: ciclo sem itens selecionados). Não é incorreto — o conteúdo gravado é idêntico ao do
  `config.toml` — só é uma escrita em disco redundante que o nome do teste
  (`test_loop_nao_grava_token_quando_nao_ha_renovacao`) sugere não deveria acontecer; o teste
  não cobre esse caso real porque usa `_cliente_de` mockado.
- Demais pontos revistos, sem ressalva: `Token` é `frozen=True` (`cliente_shopee.py:26`),
  então `cliente.token != token_anterior` compara por valor, não identidade — correto para
  detectar renovação; `_persistir_token`/`_carregar_token` usam o mesmo idioma atômico de
  `estado.py` (tmp + `os.replace`); `datetime.fromisoformat(token.expira_em.isoformat())`
  faz round-trip exato em Python 3.11+, sem perda de precisão testada em
  `test_persistir_e_carregar_token_faz_roundtrip`. Reexecutei
  `pytest tests/test_ciclo.py -q` → 13 passed; `ruff check ciclo.py __main__.py` → All
  checks passed.

### Ciclo 1

- **[crítica]** `src/shopee_rodizio/ciclo.py:29-37` e `src/shopee_rodizio/__main__.py:52-64`
  — o token renovado (`cliente.token`, mutado in-place por
  `ClienteShopee._aplicar_renovacao`, ver `cliente_shopee.py:114/139`) nunca é lido nem
  persistido em disco por este módulo. RF-02 (`_gestao/ESPECIFICACAO.md:78-81`) exige
  "renova o `access_token`... automaticamente antes de expirar, **persistindo o token
  renovado**"; o próprio docstring de `cliente_shopee.py:4-8` documenta a invariante
  "reinício do processo não pode perder um `refresh_token`". T-004
  (`_gestao/tarefas/T-004-cliente-shopee.md:72-76`) e T-005
  (`_gestao/tarefas/T-005-boost.md:133-138`) já registraram, em revisões anteriores e
  aprovadas, que essa persistência ficaria explicitamente a cargo de T-008 ("quem orquestra
  o ciclo (T-008) ainda tem acesso ao token renovado via `cliente.token` depois de chamar
  `impulsionar()`"). **Cenário de falha concreto:** RF-08/T-009 configuram
  `Restart=on-failure` no systemd — o processo reinicia em produção (crash, deploy, reboot
  do BTT Pi) com frequência plausível num serviço 24/7 cujo `access_token` já expira a cada
  ~4h. Se um restart ocorrer depois de uma renovação bem-sucedida, `_cliente_de(config)`
  (`__main__.py:36`) reconstrói o cliente com o `refresh_token` ANTIGO ainda gravado em
  `config.toml` — o mesmo que a renovação anterior pode já ter invalidado — e a
  autenticação passa a falhar permanentemente até intervenção manual do usuário no portal
  Shopee. Não é hipotético: é exatamente a invariante que `cliente_shopee.py` foi desenhado
  para preservar, e que o módulo "que junta tudo" deveria fechar.
- Demais pontos, sem ressalva: `executar_ciclo` acumula `estado = registrar_boost(...)` a
  cada item (não perde registros dentro do ciclo); `from . import boost` (módulo, não
  função) é necessário para `patch.object(boost, "impulsionar", ...)` funcionar, e está
  documentado; `test_loop_principal_continua_apos_ciclo_lancar_excecao_inesperada` faz
  `patch("shopee_rodizio.__main__.executar_ciclo", ...)`, que funciona porque `__main__.py`
  chama o nome importado no próprio módulo, não uma referência já vinculada — confirmado
  lendo `__main__.py:58`. `_config_arquivo` usa caminhos absolutos em `tmp_path` (o achado
  de arquivo vazado na raiz do repo, descrito nas Notas, já foi corrigido antes do commit —
  `git status` confirma repositório limpo). Reexecutei: `pytest tests/test_ciclo.py -q` → 7
  passed; `ruff check ciclo.py __main__.py` → All checks passed!.

### Ciclo 3 (testador)

Verificação: todos os critérios de aceite foram executados e aprovados. A implementação de
persistência do token (RF-02) realizada no ciclo 2 foi validada por mutação: desabilitando
`_persistir_token()` intentcionalmente, os dois testes de persistência falham com a asserção
correta ("arquivo não foi gravado"), provando que os testes novos realmente detectam o
comportamento esperado — não são falsos positivos. Sem regressão na suíte completa (53 passed).
