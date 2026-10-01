"""Próximo feriado nacional via API REST da BrasilAPI (gratuita, sem chave de acesso)."""

from __future__ import annotations

from datetime import date

import requests

from .modelos import Feriado

URL_FERIADOS = "https://brasilapi.com.br/api/feriados/v1/{ano}"
DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def encontrar_proximo(feriados: list[dict], hoje: date) -> Feriado | None:
    """Retorna o primeiro feriado a partir de hoje (inclusive), ou None se não houver."""
    futuros = sorted(
        (date.fromisoformat(f["date"]), f["name"])
        for f in feriados
        if date.fromisoformat(f["date"]) >= hoje
    )
    if not futuros:
        return None

    data, nome = futuros[0]
    return Feriado(
        nome=nome,
        data=data,
        dia_semana=DIAS_SEMANA[data.weekday()],
        dias_restantes=(data - hoje).days,
    )


def buscar_proximo_feriado(sessao: requests.Session, hoje: date | None = None) -> Feriado | None:
    hoje = hoje or date.today()
    # Se já passaram todos os feriados do ano (ex.: 26/12), consultamos o ano seguinte.
    for ano in (hoje.year, hoje.year + 1):
        resposta = sessao.get(URL_FERIADOS.format(ano=ano))
        resposta.raise_for_status()
        feriado = encontrar_proximo(resposta.json(), hoje)
        if feriado:
            return feriado
    return None
