"""Manchetes do dia, extraídas de um feed RSS com BeautifulSoup (web scraping)."""

from __future__ import annotations

from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup

from .modelos import Noticia

TAMANHO_RESUMO = 160


def _limpar_resumo(descricao_html: str) -> str:
    """A <description> do feed vem com HTML (imagens, <br>). Extraímos só o texto."""
    texto = BeautifulSoup(descricao_html, "html.parser").get_text(" ", strip=True)
    texto = " ".join(texto.split())
    if len(texto) > TAMANHO_RESUMO:
        texto = texto[:TAMANHO_RESUMO].rsplit(" ", 1)[0] + "…"
    return texto


def parse_feed(xml: bytes | str, limite: int) -> list[Noticia]:
    sopa = BeautifulSoup(xml, "xml")
    noticias = []
    vistos = set()
    for item in sopa.find_all("item"):
        if len(noticias) >= limite:
            break
        titulo = item.find("title")
        link = item.find("link")
        if not titulo or not link:
            continue

        # O feed às vezes repete a mesma matéria (mesmo título, links diferentes); mostramos só uma vez.
        chave = titulo.get_text(strip=True).casefold()
        if chave in vistos:
            continue
        vistos.add(chave)

        descricao = item.find("description")
        data = item.find("pubDate")
        noticias.append(
            Noticia(
                titulo=titulo.get_text(strip=True),
                link=link.get_text(strip=True),
                resumo=_limpar_resumo(descricao.get_text()) if descricao else "",
                publicado_em=parsedate_to_datetime(data.get_text(strip=True)) if data else None,
            )
        )
    return noticias


def buscar_noticias(sessao: requests.Session, url_feed: str, limite: int = 5) -> list[Noticia]:
    resposta = sessao.get(url_feed)
    resposta.raise_for_status()
    return parse_feed(resposta.content, limite)
