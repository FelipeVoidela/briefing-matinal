"""Cotações de moedas via APIs REST gratuitas, sem chave de acesso.

Fonte principal: AwesomeAPI (cotação em tempo real, com mínima e máxima do dia).
Fontes reserva, usadas se a principal falhar (ex.: limite de requisições em servidores na nuvem):
  - Frankfurter: taxas de referência do Banco Central Europeu (moedas tradicionais, fechamento diário);
  - CoinGecko: criptomoedas, com variação das últimas 24 horas.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import requests

from .modelos import Cotacao

log = logging.getLogger("briefing")

URL_COTACOES = "https://economia.awesomeapi.com.br/json/last/{pares}"
URL_FRANKFURTER = "https://api.frankfurter.dev/v1/{inicio}.."
URL_COINGECKO = "https://api.coingecko.com/api/v3/simple/price"

FONTE_PRINCIPAL = "AwesomeAPI"
FONTE_BCE = "Banco Central Europeu (fechamento diário)"
FONTE_COINGECKO = "CoinGecko"

CRIPTOMOEDAS = {"BTC": ("bitcoin", "Bitcoin"), "ETH": ("ethereum", "Ethereum")}
NOMES_MOEDAS = {
    "USD": "Dólar Americano",
    "EUR": "Euro",
    "GBP": "Libra Esterlina",
    "JPY": "Iene Japonês",
    "CAD": "Dólar Canadense",
    "CHF": "Franco Suíço",
    "AUD": "Dólar Australiano",
    "CNY": "Yuan Chinês",
    "MXN": "Peso Mexicano",
}


# --------------------------------------------------------------------------- AwesomeAPI (principal)

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


def _buscar_awesomeapi(sessao: requests.Session, pares: list[str]) -> list[Cotacao]:
    resposta = sessao.get(URL_COTACOES.format(pares=",".join(pares)))
    # A AwesomeAPI responde 404 quando algum dos pares não existe.
    if resposta.status_code == 404:
        raise ValueError(f"par de moedas inválido em {', '.join(pares)} (formato esperado: USD-BRL).")
    resposta.raise_for_status()
    return parse_cotacoes(resposta.json(), pares)


# --------------------------------------------------------------------------- fontes reserva

def parse_frankfurter(dados: dict, codigos: list[str]) -> list[Cotacao]:
    """A série vem com base BRL (1 real = X dólares); invertemos para ter o preço em reais.

    A variação compara o último fechamento disponível com o anterior.
    """
    datas = sorted(dados["rates"])
    if not datas:
        return []
    atual = dados["rates"][datas[-1]]
    anterior = dados["rates"][datas[-2]] if len(datas) > 1 else {}

    cotacoes = []
    for codigo in codigos:
        if codigo not in atual:
            continue
        valor = 1 / atual[codigo]
        variacao = (anterior[codigo] / atual[codigo] - 1) * 100 if codigo in anterior else 0.0
        cotacoes.append(
            Cotacao(
                codigo=codigo,
                nome=NOMES_MOEDAS.get(codigo, codigo),
                valor=valor,
                variacao_pct=variacao,
                atualizado_em=datetime.fromisoformat(datas[-1]),
                fonte=FONTE_BCE,
            )
        )
    return cotacoes


def parse_coingecko(dados: dict, codigos: list[str]) -> list[Cotacao]:
    cotacoes = []
    for codigo in codigos:
        identificador, nome = CRIPTOMOEDAS[codigo]
        item = dados.get(identificador)
        if not item or "brl" not in item:
            continue
        cotacoes.append(
            Cotacao(
                codigo=codigo,
                nome=nome,
                valor=float(item["brl"]),
                variacao_pct=float(item.get("brl_24h_change") or 0.0),
                atualizado_em=datetime.fromtimestamp(item.get("last_updated_at", 0)),
                fonte=FONTE_COINGECKO,
            )
        )
    return cotacoes


def _buscar_reserva(sessao: requests.Session, pares: list[str], hoje: date) -> list[Cotacao]:
    # As fontes reserva só cotam moedas em reais ("XXX-BRL").
    codigos = [par.split("-")[0] for par in pares if par.endswith("-BRL")]
    cripto = [c for c in codigos if c in CRIPTOMOEDAS]
    tradicionais = [c for c in codigos if c not in CRIPTOMOEDAS]

    encontradas: dict[str, Cotacao] = {}
    if tradicionais:
        try:
            # Uma semana de histórico garante ao menos dois fechamentos, mesmo após fins de semana e feriados.
            resposta = sessao.get(
                URL_FRANKFURTER.format(inicio=hoje - timedelta(days=7)),
                params={"base": "BRL", "symbols": ",".join(tradicionais)},
            )
            resposta.raise_for_status()
            encontradas.update((c.codigo, c) for c in parse_frankfurter(resposta.json(), tradicionais))
        except requests.RequestException:
            log.warning("Fonte reserva Frankfurter indisponível", exc_info=True)
    if cripto:
        try:
            resposta = sessao.get(
                URL_COINGECKO,
                params={
                    "ids": ",".join(CRIPTOMOEDAS[c][0] for c in cripto),
                    "vs_currencies": "brl",
                    "include_24hr_change": "true",
                    "include_last_updated_at": "true",
                },
            )
            resposta.raise_for_status()
            encontradas.update((c.codigo, c) for c in parse_coingecko(resposta.json(), cripto))
        except requests.RequestException:
            log.warning("Fonte reserva CoinGecko indisponível", exc_info=True)

    if not encontradas:
        raise RuntimeError("nem a fonte principal nem as fontes reserva responderam.")
    # Mantém a ordem pedida pelo usuário.
    return [encontradas[c] for c in codigos if c in encontradas]


def buscar_cotacoes(sessao: requests.Session, pares: list[str], hoje: date | None = None) -> list[Cotacao]:
    try:
        return _buscar_awesomeapi(sessao, pares)
    except requests.RequestException as erro:
        log.info("AwesomeAPI indisponível (%s); usando fontes reserva.", erro)
        return _buscar_reserva(sessao, pares, hoje or date.today())
