"""Carrega as configurações a partir de variáveis de ambiente (ou do arquivo .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


@dataclass
class Configuracao:
    cidade: str = "São Paulo"
    pais: str = "BR"
    moedas: list[str] = field(default_factory=lambda: ["USD-BRL", "EUR-BRL", "BTC-BRL"])
    feed_noticias: str = "https://g1.globo.com/rss/g1/"
    qtd_noticias: int = 5
    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    pasta_saida: Path = RAIZ_PROJETO / "saida"

    @property
    def telegram_configurado(self) -> bool:
        return bool(self.telegram_token and self.telegram_chat_id)


def inteiro_positivo(valor: str) -> int:
    """Converte texto em inteiro >= 1, com mensagem clara em caso de erro."""
    try:
        numero = int(valor)
    except ValueError:
        raise ValueError(f"'{valor}' não é um número inteiro.") from None
    if numero < 1:
        raise ValueError(f"o valor deve ser maior que zero (recebido: {numero}).")
    return numero


def separar_moedas(texto: str) -> list[str]:
    """'usd-brl, eur-brl,' -> ['USD-BRL', 'EUR-BRL'] (ignora espaços e itens vazios)."""
    moedas = [m.strip().upper() for m in texto.split(",") if m.strip()]
    if not moedas:
        raise ValueError("informe ao menos um par de moedas, ex.: USD-BRL.")
    return moedas


def carregar_configuracao() -> Configuracao:
    """Lê o .env (se existir) e monta a configuração, usando valores padrão quando ausentes."""
    load_dotenv(RAIZ_PROJETO / ".env")
    padrao = Configuracao()

    moedas = os.getenv("MOEDAS")
    qtd_noticias = os.getenv("QTD_NOTICIAS")
    try:
        return Configuracao(
            cidade=os.getenv("CIDADE") or padrao.cidade,
            pais=os.getenv("PAIS", padrao.pais),
            moedas=separar_moedas(moedas) if moedas else padrao.moedas,
            feed_noticias=os.getenv("FEED_NOTICIAS") or padrao.feed_noticias,
            qtd_noticias=inteiro_positivo(qtd_noticias) if qtd_noticias else padrao.qtd_noticias,
            telegram_token=os.getenv("TELEGRAM_TOKEN") or None,
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
        )
    except ValueError as erro:
        raise ValueError(f"Configuração inválida no .env: {erro}") from None
