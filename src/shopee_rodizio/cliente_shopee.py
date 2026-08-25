"""Cliente HTTP da Shopee Open Platform API v2: assinatura HMAC-SHA256, chamada
autenticada via `requests` e renovação proativa de `access_token`.

Invariantes garantidas aqui:
- nenhuma chamada sobe sem assinatura válida (`sign` na query);
- o token renovado é devolvido em `Resultado.token_renovado` para o chamador persistir
  (nunca fica só em memória — reinício do processo não pode perder um refresh_token);
- nenhuma falha de rede/API escapa como exceção: tudo vira um `Resultado` de erro.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import requests

BASE_URL = "https://partner.shopeemobile.com"
TIMEOUT_PADRAO = 30
MARGEM_RENOVACAO = timedelta(minutes=10)
PATH_RENOVACAO = "/api/v2/auth/access_token/get"


@dataclass(frozen=True)
class Token:
    access_token: str
    refresh_token: str
    expira_em: datetime | None = None


@dataclass(frozen=True)
class Resultado:
    sucesso: bool
    dados: dict | None = None
    token_renovado: Token | None = None
    erro: str | None = None


def base_publica(partner_id: int, path: str, timestamp: int) -> str:
    """Base assinada de uma chamada de nível partner (sem loja): id + path + timestamp."""
    return f"{partner_id}{path}{timestamp}"


def base_loja(
    partner_id: int, path: str, timestamp: int, access_token: str, shop_id: int
) -> str:
    """Base assinada de uma chamada de nível loja: acresce access_token + shop_id."""
    return f"{partner_id}{path}{timestamp}{access_token}{shop_id}"


def assinatura(partner_key: str, base: str) -> str:
    """HMAC-SHA256 (hex) de `base` usando `partner_key` como chave — o valor de `sign`."""
    return hmac.new(
        partner_key.encode("utf-8"), base.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _erro_api(dados: dict) -> str | None:
    """Extrai a mensagem de erro do corpo da Shopee; `None` se a resposta foi de sucesso."""
    erro = dados.get("error")
    if erro:
        mensagem = dados.get("message")
        return f"{erro}: {mensagem}" if mensagem else erro
    return None


class ClienteShopee:
    def __init__(
        self,
        partner_id: int,
        partner_key: str,
        shop_id: int,
        access_token: str,
        refresh_token: str,
        expira_em: datetime | None,
        base_url: str = BASE_URL,
        timeout: int = TIMEOUT_PADRAO,
        margem: timedelta = MARGEM_RENOVACAO,
    ) -> None:
        self._partner_id = partner_id
        self._partner_key = partner_key
        self._shop_id = shop_id
        self._token = Token(access_token, refresh_token, expira_em)
        self._base_url = base_url
        self._timeout = timeout
        self._margem = margem

    @property
    def token(self) -> Token:
        return self._token

    def chamar(self, path: str, params: dict) -> Resultado:
        """Faz uma chamada de nível loja assinada, renovando o token antes se necessário.

        Devolve sempre um `Resultado`: nenhuma exceção de rede/API escapa daqui.
        """
        token_renovado: Token | None = None
        try:
            if self._precisa_renovar():
                dados_renov = self._requisitar(
                    PATH_RENOVACAO,
                    {
                        "partner_id": self._partner_id,
                        "shop_id": self._shop_id,
                        "refresh_token": self._token.refresh_token,
                    },
                    nivel_loja=False,
                )
                erro = _erro_api(dados_renov)
                if erro:
                    return Resultado(sucesso=False, erro=erro)
                token_renovado = self._aplicar_renovacao(dados_renov)

            dados = self._requisitar(path, params, nivel_loja=True)
            erro = _erro_api(dados)
            if erro:
                # a renovação já invalidou o refresh_token antigo: o token novo precisa
                # voltar ao chamador mesmo quando a chamada-alvo falha, ou se perde.
                return Resultado(sucesso=False, erro=erro, token_renovado=token_renovado)
            return Resultado(sucesso=True, dados=dados, token_renovado=token_renovado)
        except requests.exceptions.RequestException as exc:
            return Resultado(
                sucesso=False, erro=str(exc), token_renovado=token_renovado
            )

    def _precisa_renovar(self) -> bool:
        if self._token.expira_em is None:
            return True
        return self._token.expira_em <= datetime.now(UTC) + self._margem

    def _aplicar_renovacao(self, dados: dict) -> Token:
        novo = Token(
            access_token=dados["access_token"],
            refresh_token=dados["refresh_token"],
            expira_em=datetime.now(UTC) + timedelta(seconds=dados.get("expire_in", 0)),
        )
        self._token = novo
        return novo

    def _requisitar(self, path: str, params: dict, *, nivel_loja: bool) -> dict:
        timestamp = int(datetime.now(UTC).timestamp())
        if nivel_loja:
            base = base_loja(
                self._partner_id,
                path,
                timestamp,
                self._token.access_token,
                self._shop_id,
            )
        else:
            base = base_publica(self._partner_id, path, timestamp)

        query = {
            "partner_id": self._partner_id,
            "timestamp": timestamp,
            "sign": assinatura(self._partner_key, base),
        }
        if nivel_loja:
            query["access_token"] = self._token.access_token
            query["shop_id"] = self._shop_id

        resposta = requests.post(
            self._base_url + path, params=query, json=params, timeout=self._timeout
        )
        resposta.raise_for_status()
        return resposta.json()
