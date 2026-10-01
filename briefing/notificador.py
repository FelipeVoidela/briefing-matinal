"""Envio do briefing pela API REST de bots do Telegram (requisição POST)."""

from __future__ import annotations

import requests

URL_TELEGRAM = "https://api.telegram.org/bot{token}/sendMessage"
LIMITE_CARACTERES = 4096  # tamanho máximo de uma mensagem no Telegram


def enviar_telegram(sessao: requests.Session, token: str, chat_id: str, texto: str) -> None:
    resposta = sessao.post(
        URL_TELEGRAM.format(token=token),
        json={
            "chat_id": chat_id,
            "text": texto[:LIMITE_CARACTERES],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )
    corpo = resposta.json()
    if not corpo.get("ok"):
        raise RuntimeError(f"Telegram recusou a mensagem: {corpo.get('description', resposta.text)}")
