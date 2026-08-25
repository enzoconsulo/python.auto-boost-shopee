# MAPA — shopee-rodizio

<!-- GERADO por _sistema/ferramentas/mapa.mjs. NÃO editar à mão — a próxima geração sobrescreve. HEAD: b5df182 · 2026-08-25 -->

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
src/shopee_rodizio/  __init__.py, cliente_shopee.py, config.py, estado.py
tests/  test_cliente_shopee.py, test_config.py, test_estado.py, test_scaffold.py
```

## Símbolos públicos por arquivo

### `src/shopee_rodizio/__init__.py`
- `main()`

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

### `tests/test_scaffold.py`
- `test_pacote_existe()`

## Limites deste mapa

- Extração por padrão de linha, não por AST: declaração exportada em forma incomum
  pode não aparecer aqui. Se algo que você espera não está listado, o arquivo existe
  na árvore acima — abra e leia.
- Só símbolos de TOPO e públicos. Função interna, helper e detalhe de implementação
  ficam de fora de propósito: eles são o que você lê no arquivo quando for mexer nele.
- Descrição é a primeira frase da documentação do símbolo. O resto (parâmetros,
  casos de borda, contratos) está no arquivo.
