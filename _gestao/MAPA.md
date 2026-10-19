# MAPA — shopee-rodizio

<!-- GERADO por _sistema/ferramentas/mapa.mjs. NÃO editar à mão — a próxima geração sobrescreve. HEAD: ad59a57 · 2026-10-19 (gerado por script equivalente; _sistema/ ausente nesta máquina) -->

Índice denso deste projeto: o que existe, onde, e a assinatura de cada símbolo
público. **Existe para você não precisar varrer o projeto para se orientar** — ler o
código inteiro custa ~20× mais que ler isto, e é pago em toda tarefa por todo agente.

Como usar: leia este arquivo primeiro; depois abra na íntegra **só** os arquivos que
você vai modificar ou cujo comportamento interno você precisa conferir.

## Árvore

```
(raiz)  CLAUDE.md, README.md, config.example.toml, pyproject.toml, uv.lock
_gestao/  DECISOES.md, ESPECIFICACAO.md, GUIA.md, MAPA.md, PLANO.md, PROGRESSO.md, equipe.json
_gestao/tarefas/  T-001-scaffold.md, T-002-config.md, T-003-estado.md, T-004-cliente-shopee.md, T-005-boost.md, T-006-selecao-ponderada.md, T-007-logging.md, T-008-ciclo.md, T-009-systemd-deploy.md, T-010-smoke-test.md, T-011-corrigir-lint-projeto.md, T-012-escrita-atomica-config.md, T-013-erro-sem-credencial.md, T-014-espera-na-subida.md, T-015-releitura-config-por-ciclo.md, T-016-systemd-e-logs.md, T-017-modulo-catalogo.md, T-018-cache-catalogo.md, T-019-painel-web.md, T-020-deploy-painel.md, T-021-abas-no-ar-e-relatorio.md
scripts/  definir_senha_painel.py, emprestar_token.py, esperar_porta.sh, gerar_token.py, sincronizar_itens.py, smoke_test.py
scripts/atalhos/  definir_senha_painel.sh, editar_pesos.sh, gerar_token.sh, iniciar_servico.sh, instalar_painel.sh, instalar_servico.sh, instalar_tunel.sh, parar_servico.sh, reiniciar_servico.sh, sincronizar_itens.sh, smoke_test.sh, status_servico.sh, status_tunel.sh, ver_logs.sh
src/shopee_rodizio/  __init__.py, __main__.py, armazem_token.py, arquivo.py, boost.py, catalogo.py, ciclo.py, cliente_shopee.py, config.py, estado.py, logging_config.py, painel.py, relatorio.py, selecao.py
src/shopee_rodizio/painel_web/  index.html, painel.css, painel.js
systemd/  shopee-painel.service, shopee-proxy-tunnel.service, shopee-rodizio.service
tests/  test_armazem_token.py, test_boost.py, test_catalogo.py, test_ciclo.py, test_cliente_shopee.py, test_config.py, test_config_gravacao.py, test_emprestar_token.py, test_estado.py, test_logging_config.py, test_loop_subida_e_releitura.py, test_painel.py, test_relatorio.py, test_scaffold.py, test_selecao.py
```

## Símbolos públicos por arquivo

### `scripts/definir_senha_painel.py` — Define (ou troca) a senha do painel web: grava só o hash PBKDF2 em `[painel].senha_hash`
- `main(argv: list[str] | None=None)`

### `scripts/emprestar_token.py` — Empresta o access_token da loja para outro app sem criar uma segunda cadeia de token.
- `_analisar_args(argv: list[str])`
- `main(argv: list[str] | None=None)`

### `scripts/gerar_token.py` — Troca o código de autorização da Shopee Open Platform pelo par definitivo de
- `_analisar_args(argv: list[str])`
- `_link_autorizacao(partner_id: int, partner_key: str, redirect: str)`
- `_extrair_code_e_shop_id(url_colada: str)`
- `_trocar_code_por_tokens(partner_id: int, partner_key: str, code: str, shop_id: int, proxy_https: str | None=None)`
- `_gravar_no_config(caminho: str, shop_id: int, access_token: str, refresh_token: str)`
- `main(argv: list[str] | None=None)`

### `scripts/sincronizar_itens.py` — Puxa a lista real de anúncios ativos da loja e gera o bloco `[[itens]]` do
- `_analisar_args(argv: list[str])`
- `main(argv: list[str] | None=None)`

### `scripts/smoke_test.py` — Smoke-test manual contra a API real da Shopee.
- `_analisar_args(argv: list[str])`
- `main(argv: list[str] | None=None)`

### `src/shopee_rodizio/__init__.py`
- `main()`

### `src/shopee_rodizio/__main__.py` — Entrypoint do serviço: carrega a config, configura o log e entra no loop de rodízio.
- `_analisar_args(argv: list[str])`
- `_aguardar_intervalo_desde_ultimo_ciclo(config: Config, estado: Estado)`
- `_recarregar(caminho_config: str, atual: Config, cliente: ClienteShopee, estado: Estado)`
- `executar_loop(caminho_config: str, *, max_iteracoes: int | None=None)`
- `main(argv: list[str] | None=None)`

### `src/shopee_rodizio/armazem_token.py` — Token da Shopee persistido em disco e compartilhado entre processos.
- `ArmazemToken` *(classe)*
- `caminho_token(config: Config)`
- `cliente_da_config(config: Config)`

### `src/shopee_rodizio/arquivo.py` — Primitivas de disco compartilhadas: escrita atômica durável e lock entre processos.
- `gravar_atomico(caminho: str | Path, texto: str)`
- `_fsync_diretorio(diretorio: Path)`
- `travado(caminho_lock: str | Path)`

### `src/shopee_rodizio/boost.py` — Chamada do endpoint de impulsionamento de UM item, via `cliente_shopee.py`.
- `ResultadoBoost` *(classe)*
- `impulsionar(cliente: ClienteShopee, config: Config, item_id: int)`

### `src/shopee_rodizio/catalogo.py` — Catálogo real da loja via Shopee Open Platform: anúncios ativos e seus detalhes.
- `ErroCatalogo` *(classe)*
- `ItemCatalogo` *(classe)*
- `buscar_item_ids_ativos(cliente: ClienteShopee, *, pausa: float=0.0)`
- `buscar_detalhes(cliente: ClienteShopee, item_ids: list[int], *, buscar_variacoes: bool=False, pausa: float=0.0)`
- `extrair_item(bruto: dict)`
- `_com_variacoes(cliente: ClienteShopee, item: ItemCatalogo)`
- `_resposta(dados: dict | None)`
- `_preco(bruto: dict)`
- `_estoque(bruto: dict)`
- `CacheCatalogo` *(classe)*
- `caminho_cache(caminho_estado: str | Path)`
- `carregar_cache(caminho: str | Path)`
- `gravar_cache(caminho: str | Path, cache: CacheCatalogo)`
- `baixar_catalogo(cliente: ClienteShopee, *, buscar_variacoes: bool, pausa: float=PAUSA_ENTRE_CHAMADAS, agora: datetime | None=None)`

### `src/shopee_rodizio/ciclo.py` — Orquestração de um ciclo de rodízio: seleciona itens, impulsiona cada um via
- `executar_ciclo(cliente: ClienteShopee, config: Config, estado: Estado)`

### `src/shopee_rodizio/cliente_shopee.py` — Cliente HTTP da Shopee Open Platform API v2: assinatura HMAC-SHA256, chamada
- `Token` *(classe)*
- `Resultado` *(classe)*
- `base_publica(partner_id: int, path: str, timestamp: int)`
- `base_loja(partner_id: int, path: str, timestamp: int, access_token: str, shop_id: int)`
- `assinatura(partner_key: str, base: str)`
- `mensagem_segura(exc: BaseException)`
- `_erro_api(dados: dict)`
- `ClienteShopee` *(classe)*

### `src/shopee_rodizio/config.py` — Leitura, validação e regravação (só do bloco `[[itens]]`) da configuração TOML.
- `ConfigError` *(classe)*
- `ConflitoConfig` *(classe)*
- `ShopeeCredenciais` *(classe)*
- `CicloConfig` *(classe)*
- `CaminhosConfig` *(classe)*
- `RedeConfig` *(classe)*
- `PainelConfig` *(classe)*
- `Item` *(classe)*
- `Config` *(classe)*
- `carregar_config(caminho: str | Path)`
- `_validar(dados: dict)`
- `_validar_painel(secao: dict)`
- `_validar_secao(dados: dict, nome: str, campos: tuple[str, ...])`
- `_validar_item(item: dict, indice: int)`
- `versao_config(texto: str)`
- `nomes_nos_comentarios(texto: str)`
- `regenerar_bloco_itens(texto: str, itens: list[tuple[int, int]], nomes: dict[int, str] | None=None)`
- `_linha_solta(linha: str)`
- `_nome_de_comentario(nome: str)`
- `gravar_config(caminho: str | Path, texto_novo: str, *, alteravel: tuple[tuple[str, ...], ...]=(('itens',),))`
- `_sem_chaves(dados: dict, caminhos: tuple[tuple[str, ...], ...])`
- `definir_senha_painel(caminho: str | Path, senha_hash: str)`
- `atualizar_itens(caminho: str | Path, itens: list[tuple[int, int]], nomes: dict[int, str] | None=None, versao_esperada: str | None=None)`

### `src/shopee_rodizio/estado.py` — Persistência do histórico de impulsionamentos em JSON, com escrita atômica.
- `RegistroBoost` *(classe)*
- `Estado` *(classe)*
- `carregar_estado(caminho: str | Path)`
- `registrar_boost(estado: Estado, item_id: int, sucesso: bool, mensagem: str)`
- `historico_recente(estado: Estado, item_id: int)`
- `ultimo_ciclo_em(estado: Estado, *, so_sucesso: bool=False)`
- `ancora_do_intervalo(estado: Estado)`
- `segundos_ate_proximo_ciclo(estado: Estado, intervalo_horas: float, agora: datetime | None=None)`
- `_gravar(estado: Estado)`

### `src/shopee_rodizio/logging_config.py` — Configuração do logging do projeto: arquivo com rotação por tamanho (stdlib).
- `configurar(caminho_log: str, max_bytes: int=_MAX_BYTES_PADRAO, backup_count: int=_BACKUP_COUNT_PADRAO)`

### `src/shopee_rodizio/painel.py` — Painel web local para ver o catálogo real da loja e ajustar os pesos do rodízio.
- `gerar_hash_senha(senha: str, iteracoes: int=ITERACOES_PBKDF2)`
- `verificar_senha(senha: str, senha_hash: str)`
- `cliente_permitido(ip: str, redes: tuple[str, ...])`
- `host_permitido(host: str | None, nomes_maquina: tuple[str, ...])`
- `_nomes_desta_maquina()`
- `montar_estado(config: Config, texto_config: str, cache: catalogo.CacheCatalogo, *, agora: datetime | None=None, erro_catalogo: str | None=None)`
- `montar_relatorio(config: Config, texto_config: str, cache: catalogo.CacheCatalogo, dias: int, *, agora: datetime | None=None)`
- `dias_do_pedido(query: str)`
- `PedidoInvalido` *(classe)*
- `validar_pesos(corpo: object, ids_conhecidos: set[int])`
- `Painel` *(classe)*
- `criar_handler(painel: Painel)`
- `criar_servidor(caminho_config: str | Path, endereco: str, porta: int)`
- `_analisar_args(argv: list[str])`
- `main(argv: list[str] | None=None)`

### `src/shopee_rodizio/relatorio.py` — Leitura do histórico (`estado.json`) para as abas "No ar agora" e "Relatório" do painel.
- `_Registro` *(classe)*
- `_registros(estado: Estado)`
- `_ciclos(registros: list[_Registro])`
- `no_ar_agora(estado: Estado, agora: datetime | None=None)`
- `relatorio(estado: Estado, dias: int, pesos_atuais: dict[int, int], agora: datetime | None=None)`
- `_linha_item(item_id: int, peso: int | None)`
- `_erro_resumido(mensagem: str)`

### `src/shopee_rodizio/selecao.py` — Sorteio ponderado de itens, sem reposição, para um único ciclo de boost.
- `selecionar(itens: list[Item], limite_slots: int, rng: random.Random=random)`

### `tests/test_armazem_token.py` — Testes de `armazem_token.py`: token.json compartilhado entre processos.
- `_config(tmp_path)`
- `test_gravar_e_carregar_faz_roundtrip_sem_deixar_temporario(tmp_path)`
- `test_carregar_sem_arquivo_devolve_none(tmp_path)`
- `test_travado_so_libera_outro_interessado_depois_de_solto(tmp_path)`
- `test_caminho_token_fica_ao_lado_do_estado(tmp_path)`
- `test_cliente_da_config_usa_token_json_em_vez_do_config_apos_restart(tmp_path)`
- `test_cliente_da_config_sem_token_json_usa_config(tmp_path)`

### `tests/test_boost.py`
- `_config(**overrides_ciclo)`
- `test_impulsionar_com_sucesso_devolve_resultado_positivo()`
- `test_impulsionar_usa_endpoint_e_shop_id_da_config()`
- `test_impulsionar_erro_da_api_devolve_resultado_negativo_sem_lancar()`
- `test_impulsionar_erro_sem_mensagem_devolve_mensagem_generica()`

### `tests/test_catalogo.py` — Testes de `catalogo.py` com um cliente fake (sem rede) e do script que o consome.
- `_ClienteFake` *(classe)*
- `_ok(response: dict)`
- `test_lista_ids_ativos_paginando_ate_o_fim()`
- `test_falha_em_qualquer_pagina_da_listagem_lanca_erro_catalogo()`
- `test_extrai_nome_imagem_preco_estoque_e_status()`
- `test_estoque_no_formato_legado_stock_info_tambem_e_lido()`
- `test_item_sem_preco_nem_estoque_vira_none_sem_erro()`
- `test_variacoes_so_sao_buscadas_quando_pedido_e_agregam_preco_e_estoque()`
- `test_lote_de_detalhes_que_falha_e_pulado_sem_lancar()`
- `test_detalhes_em_lotes_de_50()`
- `_script_sincronizar()`
- `test_sincronizar_preserva_pesos_e_secao_rede_depois_dos_itens(tmp_path)`
- `test_cache_roundtrip_e_vencimento(tmp_path)`
- `test_cache_ausente_ou_corrompido_vira_vazio_e_vencido(tmp_path)`
- `test_baixar_catalogo_mantem_item_ativo_sem_detalhe()`

### `tests/test_ciclo.py` — Testes de `ciclo.py`: orquestração de um ciclo de rodízio, sem depender de rede real.
- `_config(itens: list[Item], limite_slots: int=2)`
- `_estado(tmp_path)`
- `_itens(*ids: int)`
- `test_ciclo_com_todos_os_boosts_com_sucesso_grava_historico(tmp_path)`
- `test_ciclo_com_boost_falhando_por_erro_de_api_nao_lanca_e_grava_falha(tmp_path)`
- `test_ciclo_com_excecao_inesperada_de_rede_nao_escapa_e_grava_falha(tmp_path)`
- `test_ciclo_com_falha_ao_gravar_historico_nao_escapa(tmp_path)`
- `test_ciclo_respeita_limite_de_slots_e_seleciona_via_selecao(tmp_path)`
- `test_ciclo_sem_itens_selecionados_nao_grava_nada(tmp_path)`
- `_config_arquivo(tmp_path)`
- `test_loop_principal_roda_numero_limitado_de_iteracoes_sem_quebrar(tmp_path, _config_arquivo)`
- `test_loop_principal_continua_apos_ciclo_lancar_excecao_inesperada(tmp_path, _config_arquivo)`
- `_resposta(json_dados: dict)`
- `test_loop_grava_token_renovado_em_token_json_ao_lado_do_estado(_config_arquivo)`
- `test_loop_sobe_com_token_json_em_vez_do_config_apos_restart(_config_arquivo)`
- `test_loop_primeira_subida_sem_renovacao_nao_grava_token_com_cliente_real(tmp_path, _config_arquivo)`

### `tests/test_cliente_shopee.py`
- `_cliente(**overrides)`
- `_resposta(json_dados: dict, status_ok: bool=True)`
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
- `test_chamar_com_metodo_get_manda_params_na_query_sem_corpo(get_mock)`
- `test_chamar_com_proxy_configurado_manda_proxies_na_chamada(post_mock)`
- `test_chamar_sem_proxy_configurado_nao_manda_proxies(post_mock)`
- `test_token_property_reflete_estado_atual_do_cliente()`
- `_renovacao()`
- `_ok()`
- `test_chamar_com_armazem_usa_o_token_mais_novo_do_disco(post_mock, tmp_path)`
- `test_chamar_com_armazem_grava_token_renovado_no_disco_na_hora(post_mock, tmp_path)`
- `_ArmazemComRenovacaoConcorrente` *(classe)*
- `test_renovacao_feita_por_outro_processo_durante_o_lock_nao_renova_de_novo(post_mock, tmp_path)`
- `test_garantir_token_com_margem_maior_renova_token_ainda_valido(post_mock)`
- `test_garantir_token_valido_dentro_da_margem_nao_chama_a_api(post_mock)`
- `_ArmazemQueFalhaNaPrimeiraGravacao` *(classe)*
- `test_falha_ao_gravar_token_renovado_nao_perde_o_token_e_regrava_depois(post_mock, tmp_path)`
- `_erro_http_com_url_assinada()`
- `test_chamar_erro_http_nao_vaza_access_token_nem_sign_na_mensagem(post_mock)`
- `test_falha_na_renovacao_nao_vaza_refresh_token_na_mensagem(post_mock)`
- `test_mensagem_segura_preserva_mensagem_sem_segredo()`

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
- `test_config_sem_secao_rede_tem_proxy_https_none(tmp_path)`
- `test_config_com_secao_rede_carrega_proxy_https(tmp_path)`

### `tests/test_config_gravacao.py` — Testes da regravação do `[[itens]]` do config.toml (`config.py`) e de `arquivo.py`.
- `test_regenerar_preserva_secao_depois_dos_itens_e_seu_comentario()`
- `test_regenerar_sem_itens_anexa_no_fim()`
- `test_regenerar_junta_blocos_de_itens_separados_por_outra_secao()`
- `test_regenerar_nome_com_quebra_de_linha_nao_quebra_o_toml()`
- `test_nomes_nos_comentarios_le_o_que_a_regeneracao_escreve()`
- `test_atualizar_itens_grava_e_preserva_nomes_existentes(tmp_path)`
- `test_atualizar_itens_com_versao_desatualizada_lanca_conflito_e_nao_grava(tmp_path)`
- `test_atualizar_itens_sem_nenhum_item_e_recusado_sem_tocar_no_arquivo(tmp_path)`
- `test_gravar_config_recusa_texto_que_muda_outra_secao(tmp_path)`
- `test_gravar_atomico_nao_deixa_temporario_e_preserva_modo(tmp_path)`
- `test_config_sem_secao_painel_usa_padroes(tmp_path)`
- `test_config_com_porta_do_painel_invalida_e_recusada(tmp_path)`

### `tests/test_emprestar_token.py` — Testes de `scripts/emprestar_token.py`, sem rede real.
- `emprestar()`
- `config_toml(tmp_path)`
- `_gravar_token(tmp_path, validade: timedelta)`
- `_resposta(json_dados: dict)`
- `test_token_valido_pelo_tempo_pedido_e_emprestado_sem_renovar(post_mock, emprestar, config_toml, tmp_path, capsys)`
- `test_token_perto_de_vencer_e_renovado_e_gravado_antes_de_emprestar(post_mock, emprestar, config_toml, tmp_path, capsys)`
- `test_falha_ao_renovar_sai_com_erro_sem_imprimir_token(post_mock, emprestar, config_toml, tmp_path, capsys)`
- `test_minutos_perto_da_validade_do_token_e_recusado(emprestar, config_toml, capsys)`

### `tests/test_estado.py`
- `test_primeira_execucao_sem_arquivo_previo_nao_lanca_erro(tmp_path)`
- `test_registrar_boost_grava_e_carregar_estado_relê_o_historico(tmp_path)`
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

### `tests/test_loop_subida_e_releitura.py` — Testes do loop de `__main__.py`: espera na subida (sem queimar ciclo a cada restart) e
- `_estado_com(*momentos: datetime)`
- `test_sem_historico_o_primeiro_ciclo_roda_na_hora()`
- `test_restart_2h20_depois_do_ultimo_ciclo_espera_1h40()`
- `test_ultimo_ciclo_ha_mais_de_um_intervalo_roda_na_hora()`
- `test_relogio_atrasado_sem_rtc_espera_o_intervalo_cheio()`
- `_r(atras: timedelta, sucesso: bool)`
- `test_falhas_depois_do_ultimo_sucesso_nao_empurram_o_proximo_ciclo()`
- `test_sucesso_ha_mais_de_um_intervalo_e_falha_recente_roda_na_hora()`
- `test_relogio_atrasado_vale_mesmo_quando_o_registro_futuro_e_uma_falha()`
- `test_timestamp_ilegivel_e_ignorado()`
- `_toml(tmp_path, pesos: dict[int, int])`
- `config_arquivo(tmp_path)`
- `_ok(*_args, **_kwargs)`
- `test_loop_com_ciclo_recente_no_historico_dorme_o_restante_antes_do_primeiro_ciclo(tmp_path, config_arquivo)`
- `test_loop_rele_config_a_cada_ciclo_e_usa_itens_novos_sem_reiniciar(tmp_path, config_arquivo)`
- `test_loop_com_config_invalido_no_meio_segue_com_a_ultima_config_valida(tmp_path, config_arquivo)`
- `test_loop_so_recria_cliente_quando_credenciais_mudam(tmp_path, config_arquivo)`

### `tests/test_painel.py` — Testes do painel web (`painel.py`): servidor real numa thread, sem rede externa.
- `_toml(tmp_path, senha_hash: str | None)`
- `ambiente(tmp_path)`
- `_pedir(porta, metodo, caminho, *, senha=SENHA, corpo=None, cabecalhos=None, host=None)`
- `test_senha_hash_roundtrip_e_senha_errada()`
- `test_so_clientes_da_rede_local_sao_atendidos(ip, permitido)`
- `test_host_precisa_ser_ip_ou_nome_da_maquina_contra_dns_rebinding()`
- `test_sem_senha_responde_401_e_nao_entrega_nada(ambiente)`
- `test_senha_errada_responde_401(ambiente)`
- `test_host_estranho_e_recusado(ambiente)`
- `test_pagina_e_estado_sem_nenhuma_credencial(ambiente)`
- `test_post_sem_header_do_painel_e_recusado_contra_csrf(ambiente)`
- `test_gravar_pesos_atualiza_config_e_preserva_o_resto(ambiente)`
- `test_gravar_com_versao_antiga_responde_409_e_nao_grava(ambiente)`
- `test_pedido_invalido_responde_400_sem_tocar_no_config(ambiente, itens)`
- `test_atualizar_catalogo_usa_cliente_do_token_json_e_respeita_intervalo_minimo(ambiente)`
- `test_falha_ao_atualizar_catalogo_mantem_cache_e_mostra_erro(ambiente)`
- `test_sem_senha_configurada_o_painel_nao_atende(tmp_path)`
- `test_definir_senha_cria_secao_painel_sem_mexer_no_resto(tmp_path)`
- `test_relatorio_responde_agregados_com_nomes_e_sem_credenciais(ambiente)`
- `test_relatorio_exige_senha(ambiente)`

### `tests/test_relatorio.py` — Testes de `relatorio.py`: agregados do histórico para as abas do painel.
- `_r(item_id: int, atras: timedelta, sucesso: bool=True, mensagem: str='ok')`
- `_estado(*registros: RegistroBoost)`
- `test_no_ar_agora_lista_so_sucessos_dentro_das_4h_ordenados_por_expiracao()`
- `test_ultimo_ciclo_agrupa_registros_proximos_e_ignora_ciclos_anteriores()`
- `test_sem_historico_nada_no_ar_e_sem_ultimo_ciclo()`
- `test_relatorio_resume_periodo_e_ignora_o_que_e_mais_antigo()`
- `test_relatorio_por_dia_usa_fuso_de_brasilia_e_tem_um_ponto_por_dia()`
- `test_relatorio_por_item_compara_parte_dos_boosts_com_parte_do_peso()`
- `test_erro_http_e_resumido_sem_url()`
- `test_dias_do_pedido_aceita_so_periodos_conhecidos()`

### `tests/test_scaffold.py`
- `test_pacote_existe()`

### `tests/test_selecao.py`
- `_itens(*pesos: int)`
- `test_nunca_repete_item_dentro_do_mesmo_sorteio()`
- `test_respeita_limite_de_slots()`
- `test_limite_maior_ou_igual_ao_numero_de_itens_devolve_todos()`
- `test_item_de_peso_maior_e_escolhido_com_frequencia_maior()`

## Limites deste mapa

- Só símbolos de TOPO (funções e classes). Métodos e detalhe de implementação ficam de
  fora de propósito: eles são o que você lê no arquivo quando for mexer nele.
- Descrição é a primeira linha da documentação do módulo. O resto (parâmetros,
  casos de borda, contratos) está no arquivo.
