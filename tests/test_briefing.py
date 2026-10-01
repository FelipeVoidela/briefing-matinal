"""Testes da lógica de transformação, sem acesso à rede (usam respostas de exemplo)."""

from datetime import date, datetime

from briefing.cambio import parse_cotacoes
from briefing.clima import gerar_dicas
from briefing.feriados import encontrar_proximo
from briefing.formatacao import formatar_moeda, formatar_variacao
from briefing.modelos import Briefing, Clima
from briefing.noticias import parse_feed
from briefing.relatorio import gerar_texto_telegram


def _clima(**alteracoes) -> Clima:
    base = dict(
        cidade="São Paulo", estado="São Paulo", temperatura=22, sensacao=22, umidade=60,
        vento_kmh=10, descricao="Céu limpo", emoji="☀️", maxima=25, minima=18,
        chance_chuva=0, indice_uv=3, nascer_sol="05:45", por_sol="18:10",
    )
    base.update(alteracoes)
    return Clima(**base)


def test_dicas_chuva_e_uv():
    dicas = gerar_dicas(_clima(chance_chuva=80, indice_uv=9))
    assert any("guarda-chuva" in d for d in dicas)
    assert any("protetor" in d for d in dicas)


def test_dicas_tempo_tranquilo():
    assert gerar_dicas(_clima()) == ["😎 Tempo tranquilo hoje. Aproveite o dia!"]


def test_dicas_frio():
    assert any("casaco" in d for d in gerar_dicas(_clima(minima=8, maxima=15)))


def test_parse_cotacoes():
    dados = {
        "USDBRL": {
            "code": "USD", "name": "Dólar Americano/Real Brasileiro", "bid": "5.2271",
            "pctChange": "-0.83", "high": "5.2366", "low": "5.1702", "create_date": "2026-10-01 18:27:45",
        }
    }
    [cotacao] = parse_cotacoes(dados, ["USD-BRL", "EUR-BRL"])
    assert cotacao.nome == "Dólar Americano"
    assert cotacao.valor == 5.2271
    assert cotacao.variacao_pct == -0.83
    assert cotacao.atualizado_em == datetime(2026, 10, 1, 18, 27, 45)


def test_parse_feed_remove_html_do_resumo():
    xml = """<?xml version="1.0"?><rss><channel>
      <item>
        <title><![CDATA[Manchete de teste]]></title>
        <link>https://exemplo.com/1</link>
        <description><![CDATA[<img src="x.jpg" /><br />Texto   do resumo]]></description>
        <pubDate>Wed, 01 Oct 2026 10:00:00 -0300</pubDate>
      </item>
      <item><title>Segunda</title><link>https://exemplo.com/2</link></item>
    </channel></rss>"""
    noticias = parse_feed(xml, limite=1)
    assert len(noticias) == 1
    assert noticias[0].titulo == "Manchete de teste"
    assert noticias[0].resumo == "Texto do resumo"
    assert noticias[0].publicado_em.day == 1


def test_proximo_feriado():
    feriados = [
        {"date": "2026-09-07", "name": "Independência do Brasil"},
        {"date": "2026-11-02", "name": "Finados"},
        {"date": "2026-10-12", "name": "Nossa Senhora Aparecida"},
    ]
    feriado = encontrar_proximo(feriados, date(2026, 10, 1))
    assert feriado.nome == "Nossa Senhora Aparecida"
    assert feriado.dias_restantes == 11
    assert feriado.dia_semana == "segunda-feira"


def test_sem_feriados_restantes():
    assert encontrar_proximo([{"date": "2026-01-01", "name": "Ano Novo"}], date(2026, 12, 31)) is None


def test_formatacao_brasileira():
    assert formatar_moeda(5.2271) == "R$ 5,2271"
    assert formatar_moeda(612345.6) == "R$ 612.345,60"
    assert formatar_variacao(-0.8314) == "▼ 0,83%"


def test_texto_telegram_escapa_html():
    briefing = Briefing(gerado_em=datetime(2026, 10, 1, 7, 0), clima=_clima(cidade="A<B"))
    texto = gerar_texto_telegram(briefing)
    assert texto.startswith("<b>Bom dia!")
    assert "A&lt;B" in texto


def test_dicas_usam_valores_arredondados():
    # UV 5,6 aparece como "6" na tela, então a dica de protetor também deve aparecer.
    assert any("protetor" in d for d in gerar_dicas(_clima(indice_uv=5.6)))
