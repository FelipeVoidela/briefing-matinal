"""Cotações de moedas via API REST da AwesomeAPI (gratuita, sem chave de acesso)."""

from __future__ import annotations

from datetime import datetime

import requests

from .modelos import Cotacao

URL_COTACOES = "https://economia.awesomeapi.com.br/json/last/{pares}"


def parse_cotacoes(dados: dict, pares: list[str]) -> list[Cotacao]:
    """A API responde com chaves sem hífen ("USD-BRL" vira "USDBRL") e valores em texto."""
    cotacoes = []
    for par in pares:
        item = dados.get(par.replace("-", ""))
        if not item:
            continue
        cotacoes.append(
            Cotacao(
                codigo=item["code"],
                # "Dólar Americano/Real Brasileiro" -> "Dólar Americano"
                nome=item["name"].split("/")[0],
                valor=float(item["bid"]),
                variacao_pct=float(item["pctChange"]),
                maxima=float(item["high"]),
                minima=float(item["low"]),
                atualizado_em=datetime.strptime(item["create_date"], "%Y-%m-%d %H:%M:%S"),
            )
        )
    return cotacoes


def buscar_cotacoes(sessao: requests.Session, pares: list[str]) -> list[Cotacao]:
    resposta = sessao.get(URL_COTACOES.format(pares=",".join(pares)))
    resposta.raise_for_status()
    return parse_cotacoes(resposta.json(), pares)
