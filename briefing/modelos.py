"""Estruturas de dados (dataclasses) trocadas entre os coletores e os geradores de relatório."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Clima:
    cidade: str
    estado: str
    temperatura: float
    sensacao: float
    umidade: int
    vento_kmh: float
    descricao: str
    emoji: str
    maxima: float
    minima: float
    chance_chuva: int
    indice_uv: float
    nascer_sol: str
    por_sol: str


@dataclass
class Cotacao:
    codigo: str
    nome: str
    valor: float
    variacao_pct: float
    atualizado_em: datetime
    # Mínima e máxima do dia só existem na fonte principal; as fontes reserva não as informam.
    maxima: float | None = None
    minima: float | None = None
    fonte: str = "AwesomeAPI"


@dataclass
class Noticia:
    titulo: str
    link: str
    resumo: str = ""
    publicado_em: datetime | None = None


@dataclass
class Feriado:
    nome: str
    data: date
    dia_semana: str
    dias_restantes: int


@dataclass
class Briefing:
    """Resultado consolidado de uma execução. Cada seção é opcional: se uma fonte falhar,
    o erro é registrado em `erros` e o restante do briefing continua sendo gerado."""

    gerado_em: datetime
    clima: Clima | None = None
    cotacoes: list[Cotacao] = field(default_factory=list)
    noticias: list[Noticia] = field(default_factory=list)
    proximo_feriado: Feriado | None = None
    dicas: list[str] = field(default_factory=list)
    erros: dict[str, str] = field(default_factory=dict)

    @property
    def saudacao(self) -> str:
        hora = self.gerado_em.hour
        if hora < 12:
            return "Bom dia"
        if hora < 18:
            return "Boa tarde"
        return "Boa noite"
