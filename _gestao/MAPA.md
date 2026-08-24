# MAPA — shopee-rodizio

<!-- GERADO por _sistema/ferramentas/mapa.mjs. NÃO editar à mão — a próxima geração sobrescreve. HEAD: 9120c72 · 2026-08-24 -->

Índice denso deste projeto: o que existe, onde, e a assinatura de cada símbolo
público. **Existe para você não precisar varrer o projeto para se orientar** — ler o
código inteiro custa ~20× mais que ler isto, e é pago em toda tarefa por todo agente.

Como usar: leia este arquivo primeiro; depois abra na íntegra **só** os arquivos que
você vai modificar ou cujo comportamento interno você precisa conferir.

## Árvore

```
(raiz)  .gitignore, CLAUDE.md, README.md, config.example.toml, pyproject.toml, uv.lock
_gestao/  DECISOES.md, ESPECIFICACAO.md, GUIA.md, MAPA.md, PLANO.md, PROGRESSO.md, equipe.json
_gestao/tarefas/  T-001-scaffold.md, T-002-config.md, T-003-estado.md, T-004-cliente-shopee.md, T-005-boost.md, T-006-selecao-ponderada.md, T-007-logging.md, T-008-ciclo.md, T-009-systemd-deploy.md, T-010-smoke-test.md
src/shopee_rodizio/  __init__.py, config.py
tests/  test_config.py, test_scaffold.py
```

## Símbolos públicos por arquivo

### `src/shopee_rodizio/__init__.py`
- `main()`

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
