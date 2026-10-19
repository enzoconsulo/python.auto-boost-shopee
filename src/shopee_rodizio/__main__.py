"""Entrypoint do serviço: carrega a config, configura o log e entra no loop de rodízio.

Uso: `python -m shopee_rodizio [caminho/para/config.toml]` (padrão: `config.toml` no
diretório atual). A cada volta do loop, executa um ciclo (`ciclo.py`) e dorme
`ciclo.intervalo_horas` antes da próxima.

Subida sem queimar ciclo: antes do primeiro ciclo, o loop lê no `estado.json` quando foi o
último boost com sucesso (o que ocupa slot) e dorme o que falta do intervalo — um restart ou deploy no meio do intervalo não
dispara um ciclo extra contra slots de boost ainda ocupados (auditoria de 2026-10-19).

Config relida a cada ciclo: o `config.toml` é relido no início de cada volta, então
mudanças de peso/itens (painel web, `sincronizar_itens.py`, edição à mão) valem a partir do
próximo ciclo sem reiniciar o serviço. Config inválida no disco é logada e o loop segue com
a última config válida. Os escritores gravam atomicamente (`config.gravar_config`), então
esta leitura nunca vê um arquivo pela metade.

Persistência do token (RF-02): o cliente é ligado ao `token.json` compartilhado
(`armazem_token.py`) — relê o arquivo antes de cada uso e grava o token renovado na hora,
sob lock. Um restart do systemd sobe com o refresh_token fresco, e outros processos da
mesma loja (scripts, painel, `scripts/emprestar_token.py`) renovam sem invalidar a cadeia
do serviço.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import UTC, datetime, timedelta

from .armazem_token import cliente_da_config
from .ciclo import executar_ciclo
from .cliente_shopee import ClienteShopee
from .config import Config, ConfigError, carregar_config
from .estado import Estado, ancora_do_intervalo, carregar_estado, segundos_ate_proximo_ciclo
from .logging_config import configurar as configurar_logging

_logger = logging.getLogger("shopee_rodizio")

_CAMINHO_CONFIG_PADRAO = "config.toml"


def _analisar_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m shopee_rodizio",
        description="Rodízio automático de impulsionamento de anúncios na Shopee.",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=_CAMINHO_CONFIG_PADRAO,
        help=f"caminho do arquivo de configuração TOML (padrão: {_CAMINHO_CONFIG_PADRAO})",
    )
    return parser.parse_args(argv)


def _aguardar_intervalo_desde_ultimo_ciclo(config: Config, estado: Estado) -> None:
    espera = segundos_ate_proximo_ciclo(estado, config.ciclo.intervalo_horas)
    if espera <= 0:
        return
    ultimo = ancora_do_intervalo(estado)
    proximo = datetime.now(UTC) + timedelta(seconds=espera)
    _logger.info(
        "último boost com sucesso em %s; aguardando %.0f min até o próximo ciclo (%s) "
        "para não repetir boost com slots ainda ocupados",
        ultimo.isoformat(timespec="seconds"),
        espera / 60,
        proximo.isoformat(timespec="seconds"),
    )
    time.sleep(espera)


def _recarregar(
    caminho_config: str, atual: Config, cliente: ClienteShopee, estado: Estado
) -> tuple[Config, ClienteShopee, Estado]:
    """Relê o `config.toml`; em qualquer falha, mantém a config atual (nunca derruba o loop).

    O cliente só é reconstruído se credenciais, rede ou o caminho do estado mudarem: um
    cliente novo descartaria um token renovado que ainda não conseguiu ir para o disco.
    """
    try:
        nova = carregar_config(caminho_config)
    # TOML quebrado (TOMLDecodeError/UnicodeDecodeError são ValueError), campo inválido
    # (ConfigError, TypeError em comparação de tipo errado), arquivo sumido (OSError)
    except (ConfigError, OSError, ValueError, TypeError, KeyError) as exc:
        _logger.warning(
            "config.toml inválido (%s) — seguindo com a última config válida", exc
        )
        return atual, cliente, estado

    if nova.caminhos.log != atual.caminhos.log:
        configurar_logging(nova.caminhos.log)
    if (nova.shopee, nova.rede, nova.caminhos.estado) != (
        atual.shopee,
        atual.rede,
        atual.caminhos.estado,
    ):
        _logger.info("credenciais/rede/caminho do estado mudaram — recriando o cliente")
        cliente = cliente_da_config(nova)
    if nova.caminhos.estado != atual.caminhos.estado:
        estado = carregar_estado(nova.caminhos.estado)
    if nova.itens != atual.itens or nova.ciclo != atual.ciclo:
        _logger.info(
            "config.toml relido: %d item(ns) no rodízio, %d slot(s), intervalo de %sh",
            len(nova.itens),
            nova.ciclo.limite_slots,
            nova.ciclo.intervalo_horas,
        )
    return nova, cliente, estado


def executar_loop(caminho_config: str, *, max_iteracoes: int | None = None) -> None:
    """Carrega a config, configura o log e roda o loop de rodízio.

    `max_iteracoes` limita o número de voltas (usado só em teste); em produção o loop
    roda para sempre. Erro inesperado dentro de um ciclo é logado e o loop segue para a
    próxima volta (RF-06: nenhum erro de ciclo pode terminar o processo).
    """
    config = carregar_config(caminho_config)
    configurar_logging(config.caminhos.log)
    _logger.info("shopee-rodizio iniciado (config: %s)", caminho_config)

    cliente = cliente_da_config(config)
    estado = carregar_estado(config.caminhos.estado)
    _aguardar_intervalo_desde_ultimo_ciclo(config, estado)

    iteracao = 0
    while max_iteracoes is None or iteracao < max_iteracoes:
        config, cliente, estado = _recarregar(caminho_config, config, cliente, estado)
        try:
            estado = executar_ciclo(cliente, config, estado)
        except Exception:
            _logger.exception("erro inesperado no ciclo — o loop continua")
        iteracao += 1
        time.sleep(config.ciclo.intervalo_horas * 3600)


def main(argv: list[str] | None = None) -> None:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)
    executar_loop(args.config)


if __name__ == "__main__":
    main()
