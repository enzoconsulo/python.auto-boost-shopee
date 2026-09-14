"""Cliente HTTP da Shopee Open Platform API v2: assinatura HMAC-SHA256, chamada
autenticada via `requests` e renovação proativa de `access_token`.

Invariantes garantidas aqui:
- nenhuma chamada sobe sem assinatura válida (`sign` na query);
- com `armazem` (ver `armazem_token.py`), o token é relido do disco antes de cada uso e
  renovado sob lock entre processos, com o token novo gravado antes de soltar o lock — o
  refresh_token é de uso único e mais de um processo usa a mesma loja;
- o token renovado também volta em `Resultado.token_renovado`;
- nenhuma falha de rede/API/disco escapa como exceção: tudo vira um `Resultado` de erro.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from .armazem_token import ArmazemToken

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
        proxy_https: str | None = None,
        armazem: ArmazemToken | None = None,
    ) -> None:
        self._partner_id = partner_id
        self._partner_key = partner_key
        self._shop_id = shop_id
        self._token = Token(access_token, refresh_token, expira_em)
        self._base_url = base_url
        self._timeout = timeout
        self._margem = margem
        # todas as chamadas (inclusive renovação de token) saem por este proxy quando
        # configurado — fixa o IP de saída visto pela Shopee, independente do IP dinâmico
        # do host onde o serviço roda. Ver README, "IP de saída fixo".
        self._proxies = {"http": proxy_https, "https": proxy_https} if proxy_https else None
        self._armazem = armazem
        # a última gravação do token renovado falhou: até conseguir gravar, a memória tem o
        # único refresh_token válido e o disco (com o token antigo) não pode sobrescrevê-la
        self._token_nao_gravado = False

    @property
    def token(self) -> Token:
        return self._token

    def chamar(self, path: str, params: dict, *, metodo: str = "POST") -> Resultado:
        """Faz uma chamada de nível loja assinada, renovando o token antes se necessário.

        `metodo="GET"` manda `params` como query string em vez de corpo JSON — é o que os
        endpoints de LEITURA da Shopee (ex.: `get_item_list`) exigem; os de escrita
        (ex.: `boost_item`) usam o padrão `"POST"`.

        Devolve sempre um `Resultado`: nenhuma exceção de rede/API escapa daqui.
        """
        garantia = self.garantir_token()
        if not garantia.sucesso:
            return garantia
        token_renovado = garantia.token_renovado

        try:
            dados = self._requisitar(path, params, nivel_loja=True, metodo=metodo)
        except requests.exceptions.RequestException as exc:
            return Resultado(sucesso=False, erro=str(exc), token_renovado=token_renovado)

        erro = _erro_api(dados)
        if erro:
            # a renovação já invalidou o refresh_token antigo: o token novo precisa
            # voltar ao chamador mesmo quando a chamada-alvo falha, ou se perde.
            return Resultado(sucesso=False, erro=erro, token_renovado=token_renovado)
        return Resultado(sucesso=True, dados=dados, token_renovado=token_renovado)

    def garantir_token(self, margem: timedelta | None = None) -> Resultado:
        """Garante um access_token válido por pelo menos `margem` (padrão: a margem do
        cliente), renovando se preciso. Sucesso sem renovação devolve `token_renovado=None`.

        Com `armazem`, relê o token do disco antes e renova sob o lock entre processos,
        gravando o token novo antes de soltá-lo. Nunca lança.
        """
        margem = self._margem if margem is None else margem
        try:
            if self._armazem is None:
                return self._renovar_se_preciso(margem)

            self._recarregar_do_armazem()
            if not self._token_nao_gravado and not self._precisa_renovar(margem):
                return Resultado(sucesso=True)

            with self._armazem.travado():
                # outro processo pode ter renovado enquanto esperávamos o lock
                self._recarregar_do_armazem()
                if self._token_nao_gravado:
                    self._gravar_no_armazem()
                resultado = self._renovar_se_preciso(margem)
                if resultado.token_renovado is not None:
                    self._gravar_no_armazem()
                return resultado
        except (OSError, ValueError, KeyError) as exc:  # rede (RequestException é OSError), disco
            return Resultado(sucesso=False, erro=str(exc))

    def _recarregar_do_armazem(self) -> None:
        if self._token_nao_gravado:
            return
        token = self._armazem.carregar()
        if token is not None:
            self._token = token

    def _gravar_no_armazem(self) -> None:
        self._token_nao_gravado = True
        self._armazem.gravar(self._token)
        self._token_nao_gravado = False

    def _renovar_se_preciso(self, margem: timedelta) -> Resultado:
        if not self._precisa_renovar(margem):
            return Resultado(sucesso=True)
        dados = self._requisitar(
            PATH_RENOVACAO,
            {
                "partner_id": self._partner_id,
                "shop_id": self._shop_id,
                "refresh_token": self._token.refresh_token,
            },
            nivel_loja=False,
        )
        erro = _erro_api(dados)
        if erro:
            return Resultado(sucesso=False, erro=erro)
        return Resultado(sucesso=True, token_renovado=self._aplicar_renovacao(dados))

    def _precisa_renovar(self, margem: timedelta) -> bool:
        if self._token.expira_em is None:
            return True
        return self._token.expira_em <= datetime.now(UTC) + margem

    def _aplicar_renovacao(self, dados: dict) -> Token:
        novo = Token(
            access_token=dados["access_token"],
            refresh_token=dados["refresh_token"],
            expira_em=datetime.now(UTC) + timedelta(seconds=dados.get("expire_in", 0)),
        )
        self._token = novo
        return novo

    def _requisitar(
        self, path: str, params: dict, *, nivel_loja: bool, metodo: str = "POST"
    ) -> dict:
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

        if metodo == "GET":
            resposta = requests.get(
                self._base_url + path,
                params={**query, **params},
                timeout=self._timeout,
                proxies=self._proxies,
            )
        else:
            resposta = requests.post(
                self._base_url + path,
                params=query,
                json=params,
                timeout=self._timeout,
                proxies=self._proxies,
            )
        resposta.raise_for_status()
        return resposta.json()
