# MAPA — shopee-rodizio

<!-- GERADO por _sistema/ferramentas/mapa.mjs. NÃO editar à mão — a próxima geração sobrescreve. HEAD: 7da272e · 2026-08-25 -->

Índice denso deste projeto: o que existe, onde, e a assinatura de cada símbolo
público. **Existe para você não precisar varrer o projeto para se orientar** — ler o
código inteiro custa ~20× mais que ler isto, e é pago em toda tarefa por todo agente.

Como usar: leia este arquivo primeiro; depois abra na íntegra **só** os arquivos que
você vai modificar ou cujo comportamento interno você precisa conferir.

## Árvore

```
(raiz)  .gitignore, CLAUDE.md, README.md, config.example.toml, pyproject.toml, uv.lock
_gestao/  DECISOES.md, ESPECIFICACAO.md, GUIA.md, MAPA.md, PLANO.md, PROGRESSO.md, equipe.json
_gestao/tarefas/  T-001-scaffold.md, T-002-config.md, T-003-estado.md, T-004-cliente-shopee.md, T-005-boost.md, T-006-selecao-ponderada.md, T-007-logging.md, T-008-ciclo.md, T-009-systemd-deploy.md, T-010-smoke-test.md, T-011-corrigir-lint-projeto.md
src/shopee_rodizio/  __init__.py, __main__.py, boost.py, ciclo.py, cliente_shopee.py, config.py, estado.py, logging_config.py, selecao.py
tests/  test_boost.py, test_ciclo.py, test_cliente_shopee.py, test_config.py, test_estado.py, test_logging_config.py, test_scaffold.py, test_selecao.py
```

## Símbolos públicos por arquivo

### `src/shopee_rodizio/__init__.py`
- `main()`

### `src/shopee_rodizio/__main__.py` — Entrypoint do serviço: carrega a config, configura o log e entra no loop de rodízio.
- `_analisar_args(argv: list[str])`
- `_cliente_de(config: Config)`
- `executar_loop(caminho_config: str, *, max_iteracoes: int | None = None)`
- `main(argv: list[str] | None = None)`

### `src/shopee_rodizio/boost.py` — Chamada do endpoint de impulsionamento de UM item, via `cliente_shopee.py`.
- `ResultadoBoost` *(classe)*
- `impulsionar(cliente: ClienteShopee, config: Config, item_id: int)`

### `src/shopee_rodizio/ciclo.py` — Orquestração de um ciclo de rodízio: seleciona itens, impulsiona cada um via
- `executar_ciclo(cliente: ClienteShopee, config: Config, estado: Estado)`

### `src/shopee_rodizio/cliente_shopee.py` — Cliente HTTP da Shopee Open Platform API v2: assinatura HMAC-SHA256, chamada
- `Token` *(classe)*
- `Resultado` *(classe)*
- `base_publica(partner_id: int, path: str, timestamp: int)`
- `base_loja(partner_id: int, path: str, timestamp: int, access_token: str, shop_id: int)`
- `assinatura(partner_key: str, base: str)`
- `_erro_api(dados: dict)`
- `ClienteShopee` *(classe)*

### `src/shopee_rodizio/config.py` — Leitura e validação da configuração TOML do usuário."""
- `ConfigError` *(classe)*
- `ShopeeCredenciais` *(classe)*
- `CicloConfig` *(classe)*
- `CaminhosConfig` *(classe)*
- `Item` *(classe)*
- `Config` *(classe)*
- `carregar_config(caminho: str | Path)`
- `_validar(dados: dict)`
- `_validar_secao(dados: dict, nome: str, campos: tuple[str, ...])`
- `_validar_item(item: dict, indice: int)`

### `src/shopee_rodizio/estado.py` — Persistência do histórico de impulsionamentos em JSON, com escrita atômica."""
- `RegistroBoost` *(classe)*
- `Estado` *(classe)*
- `carregar_estado(caminho: str | Path)`
- `registrar_boost(estado: Estado, item_id: int, sucesso: bool, mensagem: str)`
- `historico_recente(estado: Estado, item_id: int)`
- `_gravar(estado: Estado)`

### `src/shopee_rodizio/logging_config.py` — Configuração do logging do projeto: arquivo com rotação por tamanho (stdlib)."""
- `configurar(caminho_log: str, max_bytes: int = _MAX_BYTES_PADRAO, backup_count: int = _BACKUP_COUNT_P…)`

### `src/shopee_rodizio/selecao.py` — Sorteio ponderado de itens, sem reposição, para um único ciclo de boost."""
- `selecionar(itens: list[Item], limite_slots: int, rng: random.Random = random)`

### `tests/test_boost.py`
- `_config(**overrides_ciclo)`
- `test_impulsionar_com_sucesso_devolve_resultado_positivo()`
- `test_impulsionar_usa_endpoint_e_shop_id_da_config()`
- `test_impulsionar_erro_da_api_devolve_resultado_negativo_sem_lancar()`
- `test_impulsionar_erro_sem_mensagem_devolve_mensagem_generica()`

### `tests/test_ciclo.py` — Testes de `ciclo.py`: orquestração de um ciclo de rodízio, sem depender de rede real."""
- `_config(itens: list[Item], limite_slots: int = 2)`
- `_estado(tmp_path)`
- `_itens(*ids: int)`
- `test_ciclo_com_todos_os_boosts_com_sucesso_grava_historico(tmp_path)`
- `test_ciclo_com_boost_falhando_por_erro_de_api_nao_lanca_e_grava_falha(tmp_path)`
- `test_ciclo_com_excecao_inesperada_de_rede_nao_escapa_e_grava_falha(tmp_path)`
- `test_ciclo_respeita_limite_de_slots_e_seleciona_via_selecao(tmp_path)`
- `test_ciclo_sem_itens_selecionados_nao_grava_nada(tmp_path)`
- `_config_arquivo(tmp_path)`
- `test_loop_principal_roda_numero_limitado_de_iteracoes_sem_quebrar(tmp_path, _config_arquivo)`
- `test_loop_principal_continua_apos_ciclo_lancar_excecao_inesperada(tmp_path, _config_arquivo)`

### `tests/test_cliente_shopee.py`
- `_cliente(**overrides)`
- `_resposta(json_dados: dict, status_ok: bool = True)`
- `test_assinatura_publica_bate_com_vetor_conhecido()`
- `test_assinatura_loja_bate_com_vetor_conhecido_e_inclui_token_e_shop()`
- `test_chamar_com_token_valido_nao_renova_e_devolve_sucesso(post_mock)`
- `test_chamar_com_token_expirado_renova_antes_e_persiste_novo_token(post_mock)`
- `test_chamar_renova_mas_alvo_falha_ainda_devolve_token_renovado_para_persistir(post_mock)`
- `test_chamar_renova_mas_timeout_no_alvo_ainda_devolve_token_renovado(post_mock)`
- `test_chamar_timeout_devolve_resultado_de_erro_sem_lancar(post_mock)`
- `test_chamar_erro_conexao_devolve_resultado_de_erro_sem_lancar(post_mock)`
- `test_chamar_erro_http_devolve_resultado_de_erro_sem_lancar(post_mock)`
- `test_chamar_corpo_de_erro_da_api_devolve_resultado_de_erro_sem_lancar(post_mock)`
- `test_chamar_falha_ao_renovar_token_devolve_erro_sem_chamar_endpoint_alvo(post_mock)`
- `test_token_property_reflete_estado_atual_do_cliente()`

### `tests/test_config.py`
- `_escrever(tmp_path: Path, conteudo: str)`
- `test_config_valida_carrega_estrutura_tipada(tmp_path)`
- `test_config_exemplo_do_projeto_e_valida()`
- `test_item_com_peso_negativo_levanta_erro_identificando_o_campo(tmp_path)`
- `test_secao_shopee_incompleta_levanta_erro_identificando_o_campo(tmp_path)`
- `test_item_sem_peso_levanta_erro(tmp_path)`
- `test_item_sem_id_levanta_erro(tmp_path)`
- `test_intervalo_horas_invalido_levanta_erro(tmp_path)`
- `test_limite_slots_invalido_levanta_erro(tmp_path)`

### `tests/test_estado.py`
- `test_primeira_execucao_sem_arquivo_previo_nao_lanca_erro(tmp_path)`
- `test_registrar_boost_grava_e_carregar_estado_rel(tmp_path)`
- `test_registrar_boost_acumula_multiplos_registros(tmp_path)`
- `test_escrita_usa_arquivo_temporario_e_nao_sobra_tmp_orfao(tmp_path)`
- `test_historico_recente_filtra_por_item_id(tmp_path)`
- `test_historico_recente_sem_registros_devolve_lista_vazia(tmp_path)`

### `tests/test_logging_config.py`
- `_limpar_handlers(logger)`
- `test_configurar_cria_arquivo_de_log_com_mensagem(tmp_path)`
- `test_configurar_formato_de_linha_inclui_timestamp_nivel_e_mensagem(tmp_path)`
- `test_configurar_rotaciona_quando_arquivo_excede_max_bytes(tmp_path)`
- `test_configurar_cria_diretorio_pai_do_log_se_nao_existir(tmp_path)`
- `test_configurar_chamado_duas_vezes_nao_duplica_handlers(tmp_path)`

### `tests/test_scaffold.py`
- `test_pacote_existe()`

### `tests/test_selecao.py`
- `_itens(*pesos: int)`
- `test_nunca_repete_item_dentro_do_mesmo_sorteio()`
- `test_respeita_limite_de_slots()`
- `test_limite_maior_ou_igual_ao_numero_de_itens_devolve_todos()`
- `test_item_de_peso_maior_e_escolhido_com_frequencia_maior()`

## Limites deste mapa

- Extração por padrão de linha, não por AST: declaração exportada em forma incomum
  pode não aparecer aqui. Se algo que você espera não está listado, o arquivo existe
  na árvore acima — abra e leia.
- Só símbolos de TOPO e públicos. Função interna, helper e detalhe de implementação
  ficam de fora de propósito: eles são o que você lê no arquivo quando for mexer nele.
- Descrição é a primeira frase da documentação do símbolo. O resto (parâmetros,
  casos de borda, contratos) está no arquivo.
