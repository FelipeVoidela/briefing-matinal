"""Apresentação do briefing em três formatos: terminal (rich), página HTML (Jinja2) e Telegram."""

from __future__ import annotations

from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .formatacao import descrever_contagem, formatar_moeda, formatar_numero, formatar_variacao
from .modelos import Briefing

PASTA_TEMPLATES = Path(__file__).parent / "templates"

_jinja = Environment(
    loader=FileSystemLoader(PASTA_TEMPLATES),
    autoescape=select_autoescape(["html"]),
)
_jinja.filters.update(
    moeda=formatar_moeda,
    variacao=formatar_variacao,
    numero=formatar_numero,
    contagem=descrever_contagem,
)


# --------------------------------------------------------------------------- terminal

def exibir_no_terminal(briefing: Briefing, console: Console | None = None) -> None:
    console = console or Console()
    data = briefing.gerado_em.strftime("%d/%m/%Y %H:%M")
    console.print(
        Panel(
            Text(f"{briefing.saudacao}! ☕  Seu briefing de {data}", justify="center", style="bold"),
            style="cyan",
        )
    )

    if briefing.clima:
        c = briefing.clima
        corpo = Group(
            Text(f"{c.emoji}  {c.descricao}", style="bold"),
            Text(
                f"🌡️  Agora: {c.temperatura:.0f}°C (sensação {c.sensacao:.0f}°C)   "
                f"↑ {c.maxima:.0f}°C  ↓ {c.minima:.0f}°C"
            ),
            Text(
                f"💧 Umidade {c.umidade}%   ☔ Chuva {c.chance_chuva}%   "
                f"💨 Vento {c.vento_kmh:.0f} km/h   🔆 UV {c.indice_uv:.0f}"
            ),
            Text(f"🌅 Nascer do sol {c.nascer_sol}   🌇 Pôr do sol {c.por_sol}"),
        )
        console.print(Panel(corpo, title=f"Clima em {c.cidade} - {c.estado}", title_align="left"))

    if briefing.dicas:
        console.print(Panel("\n".join(briefing.dicas), title="Dicas do dia", title_align="left", style="green"))

    if briefing.cotacoes:
        tabela = Table(title="💰 Câmbio", title_justify="left", expand=True)
        tabela.add_column("Moeda")
        tabela.add_column("Cotação", justify="right")
        tabela.add_column("Variação", justify="right")
        tabela.add_column("Mín / Máx do dia", justify="right")
        for cot in briefing.cotacoes:
            cor = "green" if cot.variacao_pct > 0 else "red" if cot.variacao_pct < 0 else "white"
            tabela.add_row(
                f"{cot.nome} ({cot.codigo})",
                formatar_moeda(cot.valor),
                Text(formatar_variacao(cot.variacao_pct), style=cor),
                f"{formatar_moeda(cot.minima)} / {formatar_moeda(cot.maxima)}",
            )
        console.print(tabela)

    if briefing.noticias:
        # O estilo "link" torna cada título clicável em terminais compatíveis.
        linhas = Text("\n").join(
            Text.assemble((f"{i}. ", "bold"), (n.titulo, f"link {n.link}"))
            for i, n in enumerate(briefing.noticias, 1)
        )
        console.print(Panel(linhas, title="📰 Manchetes", title_align="left"))

    if briefing.proximo_feriado:
        f = briefing.proximo_feriado
        console.print(
            Panel(
                f"🎉 {f.nome} — {f.data:%d/%m} ({f.dia_semana}), {descrever_contagem(f.dias_restantes)}",
                title="Próximo feriado",
                title_align="left",
                style="magenta",
            )
        )

    for fonte, erro in briefing.erros.items():
        console.print(f"[yellow]⚠ Não foi possível obter {fonte}: {erro}[/yellow]")


# --------------------------------------------------------------------------- HTML

def gerar_html(briefing: Briefing, pasta_saida: Path) -> Path:
    """Renderiza o template e salva em saida/briefing_AAAA-MM-DD_HHMM.html."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho = pasta_saida / f"briefing_{briefing.gerado_em:%Y-%m-%d_%H%M}.html"
    html = _jinja.get_template("briefing.html").render(b=briefing)
    caminho.write_text(html, encoding="utf-8")
    return caminho


# --------------------------------------------------------------------------- Telegram

def gerar_texto_telegram(briefing: Briefing) -> str:
    """Monta a mensagem no subconjunto de HTML aceito pelo Telegram (<b>, <i>, <a>)."""
    partes = [f"<b>{briefing.saudacao}! ☕ Briefing de {briefing.gerado_em:%d/%m/%Y}</b>"]

    if briefing.clima:
        c = briefing.clima
        partes.append(
            f"\n<b>{c.emoji} {escape(c.cidade)}</b>: {escape(c.descricao)}, {c.temperatura:.0f}°C\n"
            f"↑ {c.maxima:.0f}°C  ↓ {c.minima:.0f}°C · ☔ {c.chance_chuva}% · 🔆 UV {c.indice_uv:.0f}"
        )
    if briefing.dicas:
        partes.append("\n" + "\n".join(escape(d) for d in briefing.dicas))
    if briefing.cotacoes:
        linhas = [
            f"• {escape(cot.codigo)}: {formatar_moeda(cot.valor)} ({formatar_variacao(cot.variacao_pct)})"
            for cot in briefing.cotacoes
        ]
        partes.append("\n<b>💰 Câmbio</b>\n" + "\n".join(linhas))
    if briefing.noticias:
        linhas = [
            f'{i}. <a href="{escape(n.link)}">{escape(n.titulo)}</a>'
            for i, n in enumerate(briefing.noticias, 1)
        ]
        partes.append("\n<b>📰 Manchetes</b>\n" + "\n".join(linhas))
    if briefing.proximo_feriado:
        f = briefing.proximo_feriado
        partes.append(
            f"\n<b>🎉 Próximo feriado:</b> {escape(f.nome)} — {f.data:%d/%m} "
            f"({f.dia_semana}), {descrever_contagem(f.dias_restantes)}"
        )
    return "\n".join(partes)
