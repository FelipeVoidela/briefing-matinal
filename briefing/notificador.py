"""Envio do briefing pela API REST de bots do Telegram (requisição POST)."""

from __future__ import annotations

import requests

URL_TELEGRAM = "https://api.telegram.org/bot{token}/sendMessage"
LIMITE_CARACTERES = 4096  # tamanho máximo de uma mensagem no Telegram


def dividir_mensagem(texto: str, limite: int = LIMITE_CARACTERES) -> list[str]:
    """Quebra textos longos em várias mensagens, sempre entre linhas.

    Cortar no meio de uma linha poderia deixar uma tag <a> ou <b> aberta, e o Telegram
    recusaria a mensagem inteira. Cada linha do briefing fecha as próprias tags.
    """
    partes, atual = [], ""
    for linha in texto.split("\n"):
        candidato = f"{atual}\n{linha}" if atual else linha
        if len(candidato) <= limite:
            atual = candidato
            continue
        if atual:
            partes.append(atual)
        atual = linha[:limite]
    if atual:
        partes.append(atual)
    return partes


def enviar_telegram(sessao: requests.Session, token: str, chat_id: str, texto: str) -> None:
    for parte in dividir_mensagem(texto):
        resposta = sessao.post(
            URL_TELEGRAM.format(token=token),
            json={
                "chat_id": chat_id,
                "text": parte,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        try:
            corpo = resposta.json()
        except ValueError:
            corpo = {"ok": False, "description": f"resposta inesperada (HTTP {resposta.status_code})"}
        if not corpo.get("ok"):
            raise RuntimeError(f"Telegram recusou a mensagem: {corpo.get('description')}")
