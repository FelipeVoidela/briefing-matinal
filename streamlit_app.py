"""Briefing Matinal — versão web (Streamlit).

Reaproveita os mesmos módulos da linha de comando; só a camada de apresentação muda.
Execução local:  streamlit run streamlit_app.py
"""

from __future__ import annotations

import re

import streamlit as st

from briefing.coleta import coletar_briefing
from briefing.config import Configuracao
from briefing.formatacao import descrever_contagem, formatar_moeda, formatar_numero
from briefing.modelos import Briefing
from briefing.relatorio import renderizar_html

MOEDAS_DISPONIVEIS = {
    "USD-BRL": "🇺🇸 Dólar americano",
    "EUR-BRL": "🇪🇺 Euro",
    "GBP-BRL": "🇬🇧 Libra esterlina",
    "JPY-BRL": "🇯🇵 Iene japonês",
    "CAD-BRL": "🇨🇦 Dólar canadense",
    "CHF-BRL": "🇨🇭 Franco suíço",
    "BTC-BRL": "₿ Bitcoin",
    "ETH-BRL": "Ξ Ethereum",
}

st.set_page_config(page_title="Briefing Matinal", page_icon="☕", layout="wide")


def md(texto: str) -> str:
    """Escapa caracteres de Markdown em textos vindos de fontes externas.

    Sem isso, um "R$" viraria fórmula LaTeX e colchetes no título quebrariam os links.
    """
    return re.sub(r"([\\`*_{}\[\]()#+!|$~<>])", r"\\\1", texto)


@st.cache_data(ttl=600, show_spinner=False)
def obter_briefing(cidade: str, moedas: tuple[str, ...], qtd_noticias: int) -> Briefing:
    """Guarda o resultado por 10 minutos: recarregar a página não dispara novas chamadas às APIs."""
    config = Configuracao(cidade=cidade, moedas=list(moedas), qtd_noticias=qtd_noticias)
    return coletar_briefing(config)


# --------------------------------------------------------------------------- barra lateral

with st.sidebar:
    st.header("⚙️ Personalize")
    cidade = st.text_input("Cidade", value="São Paulo").strip() or "São Paulo"
    moedas = st.multiselect(
        "Moedas",
        options=list(MOEDAS_DISPONIVEIS),
        default=["USD-BRL", "EUR-BRL", "BTC-BRL"],
        format_func=lambda par: MOEDAS_DISPONIVEIS[par],
    )
    qtd_noticias = st.slider("Manchetes", min_value=3, max_value=10, value=5)
    if st.button("🔄 Atualizar agora", width="stretch"):
        obter_briefing.clear()
    st.caption(
        "Fontes: Open-Meteo, AwesomeAPI, BrasilAPI e g1 (RSS). "
        "Os dados ficam em cache por 10 minutos."
    )
    st.caption("[Código no GitHub](https://github.com/FelipeVoidela/briefing-matinal)")

if not moedas:
    st.sidebar.warning("Selecione ao menos uma moeda.")
    moedas = ["USD-BRL"]

with st.spinner("Consultando APIs e lendo notícias..."):
    briefing = obter_briefing(cidade, tuple(moedas), qtd_noticias)

# --------------------------------------------------------------------------- cabeçalho

st.title(f"{briefing.saudacao}! ☕")
st.caption(f"Briefing gerado em {briefing.gerado_em:%d/%m/%Y às %H:%M} (horário de Brasília)")

for fonte, erro in briefing.erros.items():
    st.warning(f"Não foi possível obter {fonte}: {md(erro)}", icon="⚠️")

# --------------------------------------------------------------------------- clima

if briefing.clima:
    c = briefing.clima
    local = f"{c.cidade} - {c.estado}" if c.estado else c.cidade
    st.subheader(f"{c.emoji} Clima em {md(local)}")
    st.write(f"**{c.descricao}** · nascer do sol {c.nascer_sol} · pôr do sol {c.por_sol}")

    col1, col2, col3, col4, col5 = st.columns(5)
    # delta_arrow="off": sensação e vento são informações extras, não variações (sem seta de alta/baixa).
    col1.metric("Agora", f"{c.temperatura:.0f}°C", f"sensação {c.sensacao:.0f}°C",
                delta_color="off", delta_arrow="off")
    col2.metric("Máx / Mín", f"{c.maxima:.0f}° / {c.minima:.0f}°")
    col3.metric("Chance de chuva", f"{c.chance_chuva}%")
    col4.metric("Índice UV", f"{c.indice_uv:.0f}")
    col5.metric("Umidade", f"{c.umidade}%", f"vento {c.vento_kmh:.0f} km/h",
                delta_color="off", delta_arrow="off")

    for dica in briefing.dicas:
        st.info(dica)

# --------------------------------------------------------------------------- câmbio

if briefing.cotacoes:
    st.subheader("💰 Câmbio")
    colunas = st.columns(len(briefing.cotacoes))
    for coluna, cot in zip(colunas, briefing.cotacoes, strict=True):
        coluna.metric(
            f"{cot.nome} ({cot.codigo})",
            formatar_moeda(cot.valor),
            f"{formatar_numero(cot.variacao_pct)}%",
            help=(f"Mínima {formatar_moeda(cot.minima)} · Máxima {formatar_moeda(cot.maxima)}"
                  if cot.maxima is not None else f"Fonte: {cot.fonte}"),
        )
    fontes = sorted({cot.fonte for cot in briefing.cotacoes} - {"AwesomeAPI"})
    if fontes:
        st.caption(f"A fonte principal (AwesomeAPI) não respondeu; cotações de: {', '.join(fontes)}.")

# --------------------------------------------------------------------------- notícias e feriado

col_noticias, col_feriado = st.columns([2, 1])

with col_noticias:
    if briefing.noticias:
        st.subheader("📰 Manchetes")
        for i, n in enumerate(briefing.noticias, 1):
            st.markdown(f"**{i}. [{md(n.titulo)}]({n.link})**")
            if n.resumo:
                st.caption(md(n.resumo))

with col_feriado:
    if briefing.proximo_feriado:
        f = briefing.proximo_feriado
        st.subheader("🎉 Próximo feriado")
        st.success(f"**{md(f.nome)}**  \n{f.data:%d/%m} ({f.dia_semana}) · {descrever_contagem(f.dias_restantes)}")

    st.download_button(
        "📄 Baixar briefing em HTML",
        data=renderizar_html(briefing),
        file_name=f"briefing_{briefing.gerado_em:%Y-%m-%d_%H%M}.html",
        mime="text/html",
        width="stretch",
    )
