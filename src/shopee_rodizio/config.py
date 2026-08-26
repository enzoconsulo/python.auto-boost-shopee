"""Leitura e validação da configuração TOML do usuário."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(Exception):
    """Configuração inválida; a mensagem identifica o campo problemático."""


@dataclass(frozen=True)
class ShopeeCredenciais:
    partner_id: int
    partner_key: str
    shop_id: int
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class CicloConfig:
    intervalo_horas: int
    limite_slots: int
    endpoint_boost: str


@dataclass(frozen=True)
class CaminhosConfig:
    log: str
    estado: str


@dataclass(frozen=True)
class RedeConfig:
    """Seção opcional: ausente em config.toml existente = sem proxy, comportamento igual
    a antes desta seção existir."""

    proxy_https: str | None = None


@dataclass(frozen=True)
class Item:
    id: int
    peso: int


@dataclass(frozen=True)
class Config:
    shopee: ShopeeCredenciais
    ciclo: CicloConfig
    caminhos: CaminhosConfig
    itens: list[Item]
    rede: RedeConfig = field(default_factory=RedeConfig)


_CAMPOS_SHOPEE = ("partner_id", "partner_key", "shop_id", "access_token", "refresh_token")
_CAMPOS_CICLO = ("intervalo_horas", "limite_slots", "endpoint_boost")
_CAMPOS_CAMINHOS = ("log", "estado")


def carregar_config(caminho: str | Path) -> Config:
    """Lê o arquivo TOML em `caminho`, valida e devolve uma `Config` tipada."""
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    return _validar(dados)


def _validar(dados: dict) -> Config:
    shopee = _validar_secao(dados, "shopee", _CAMPOS_SHOPEE)
    ciclo = _validar_secao(dados, "ciclo", _CAMPOS_CICLO)
    caminhos = _validar_secao(dados, "caminhos", _CAMPOS_CAMINHOS)

    if ciclo["intervalo_horas"] <= 0:
        raise ConfigError("ciclo.intervalo_horas deve ser > 0")
    if ciclo["limite_slots"] <= 0:
        raise ConfigError("ciclo.limite_slots deve ser > 0")

    itens_brutos = dados.get("itens")
    if not itens_brutos:
        raise ConfigError("campo ausente: itens (é preciso ao menos um [[itens]])")

    itens = [_validar_item(item, i) for i, item in enumerate(itens_brutos)]
    rede = RedeConfig(proxy_https=dados.get("rede", {}).get("proxy_https"))

    return Config(
        shopee=ShopeeCredenciais(**shopee),
        ciclo=CicloConfig(**ciclo),
        caminhos=CaminhosConfig(**caminhos),
        itens=itens,
        rede=rede,
    )


def _validar_secao(dados: dict, nome: str, campos: tuple[str, ...]) -> dict:
    secao = dados.get(nome)
    if secao is None:
        raise ConfigError(f"campo ausente: seção [{nome}]")
    for campo in campos:
        if campo not in secao:
            raise ConfigError(f"campo ausente: {nome}.{campo}")
    return {campo: secao[campo] for campo in campos}


def _validar_item(item: dict, indice: int) -> Item:
    if "id" not in item:
        raise ConfigError(f"campo ausente: itens[{indice}].id")
    if "peso" not in item:
        raise ConfigError(f"campo ausente: itens[{indice}].peso")
    if item["peso"] <= 0:
        raise ConfigError(f"itens[{indice}].peso deve ser > 0 (item id={item['id']})")
    return Item(id=item["id"], peso=item["peso"])
