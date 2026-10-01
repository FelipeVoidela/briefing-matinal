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


def carregar_configuracao() -> Configuracao:
    """Lê o .env (se existir) e monta a configuração, usando valores padrão quando ausentes."""
    load_dotenv(RAIZ_PROJETO / ".env")
    padrao = Configuracao()

    moedas = os.getenv("MOEDAS")
    return Configuracao(
        cidade=os.getenv("CIDADE", padrao.cidade),
        pais=os.getenv("PAIS", padrao.pais),
        moedas=[m.strip().upper() for m in moedas.split(",")] if moedas else padrao.moedas,
        feed_noticias=os.getenv("FEED_NOTICIAS", padrao.feed_noticias),
        qtd_noticias=int(os.getenv("QTD_NOTICIAS", padrao.qtd_noticias)),
        telegram_token=os.getenv("TELEGRAM_TOKEN") or None,
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
    )
