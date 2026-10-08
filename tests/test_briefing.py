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


def test_validacoes_de_entrada():
    import pytest

    from briefing.config import inteiro_positivo, separar_moedas
    from main import validar_horario

    assert inteiro_positivo("3") == 3
    for invalido in ("0", "-2", "abc"):
        with pytest.raises(ValueError):
            inteiro_positivo(invalido)
    assert separar_moedas(" usd-brl, ,eur-brl ") == ["USD-BRL", "EUR-BRL"]
    with pytest.raises(ValueError):
        separar_moedas(" , ")
    assert validar_horario("7:05") == "07:05"
    for invalido in ("25:99", "7h"):
        with pytest.raises(ValueError):
            validar_horario(invalido)


def test_mensagem_longa_do_telegram_e_dividida_entre_linhas():
    from briefing.notificador import dividir_mensagem

    linhas = [f'<a href="https://x.com/{i}">Notícia {i}</a>' for i in range(300)]
    partes = dividir_mensagem("\n".join(linhas), limite=500)
    assert len(partes) > 1
    assert all(len(p) <= 500 for p in partes)
    # Nenhuma tag fica aberta: cada parte tem tantos <a como </a>.
    assert all(p.count("<a ") == p.count("</a>") for p in partes)
    assert "\n".join(partes) == "\n".join(linhas)


def test_html_escapa_conteudo_externo(tmp_path):
    from briefing.modelos import Noticia
    from briefing.relatorio import gerar_html

    briefing = Briefing(gerado_em=datetime(2026, 10, 1, 7, 0),
                        noticias=[Noticia(titulo="<script>alert(1)</script>", link="https://x.com")])
    html = gerar_html(briefing, tmp_path).read_text(encoding="utf-8")
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_erros_de_rede_viram_mensagens_amigaveis():
    import requests

    from briefing.rede import descrever_erro

    assert "internet" in descrever_erro(requests.ConnectionError("detalhe técnico"))
    assert "demorou" in descrever_erro(requests.Timeout())


def test_feed_ignora_noticias_repetidas():
    xml = """<rss><channel>
      <item><title>Quina hoje</title><link>https://exemplo.com/a</link></item>
      <item><title>Quina hoje</title><link>https://exemplo.com/b</link></item>
      <item><title>Outra</title><link>https://exemplo.com/c</link></item>
    </channel></rss>"""
    # Mesmo com limite 2, a repetida é pulada e a próxima notícia diferente entra no lugar.
    assert [n.titulo for n in parse_feed(xml, limite=2)] == ["Quina hoje", "Outra"]


def test_reserva_frankfurter_inverte_taxa_e_calcula_variacao():
    from briefing.cambio import FONTE_BCE, parse_frankfurter

    dados = {"rates": {"2026-10-07": {"USD": 0.20}, "2026-10-08": {"USD": 0.19}}}
    [usd] = parse_frankfurter(dados, ["USD", "ARS"])
    assert round(usd.valor, 4) == round(1 / 0.19, 4)       # 1 real = 0,19 dólar -> 1 dólar = R$ 5,26
    assert round(usd.variacao_pct, 2) == 5.26              # dólar subiu de R$ 5,00 para R$ 5,26
    assert usd.maxima is None and usd.fonte == FONTE_BCE


def test_reserva_usada_quando_awesomeapi_falha():
    import requests

    from briefing import cambio

    class RespostaFalsa:
        def __init__(self, status, dados=None):
            self.status_code, self._dados = status, dados

        def json(self):
            return self._dados

        def raise_for_status(self):
            if self.status_code >= 400:
                erro = requests.HTTPError(f"{self.status_code}")
                erro.response = self
                raise erro

    class SessaoFalsa:
        def get(self, url, params=None):
            if "awesomeapi" in url:
                return RespostaFalsa(429)
            if "frankfurter" in url:
                return RespostaFalsa(200, {"rates": {"2026-10-07": {"USD": 0.2}, "2026-10-08": {"USD": 0.2}}})
            return RespostaFalsa(200, {"bitcoin": {"brl": 400000, "brl_24h_change": -1.5}})

    cotacoes = cambio.buscar_cotacoes(SessaoFalsa(), ["BTC-BRL", "USD-BRL"], date(2026, 10, 8))
    assert [c.codigo for c in cotacoes] == ["BTC", "USD"]   # mesma ordem pedida
    assert cotacoes[0].valor == 400000 and cotacoes[0].variacao_pct == -1.5
    assert cotacoes[1].valor == 5.0 and cotacoes[1].variacao_pct == 0.0
