"""Coleta paralela de todas as fontes. Usada tanto pela linha de comando quanto pelo app web."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo

from .cambio import buscar_cotacoes
from .clima import buscar_clima, gerar_dicas
from .config import Configuracao
from .feriados import buscar_proximo_feriado
from .modelos import Briefing
from .noticias import buscar_noticias
from .rede import criar_sessao, descrever_erro

log = logging.getLogger("briefing")

# Servidores na nuvem rodam em UTC; fixar o fuso garante a saudação e a contagem de feriados corretas.
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


def coletar_briefing(config: Configuracao) -> Briefing:
    """Consulta todas as fontes em paralelo. Uma fonte com erro não derruba as demais."""
    agora = datetime.now(FUSO_HORARIO).replace(tzinfo=None)
    tarefas = {
        "o clima": lambda s: buscar_clima(s, config.cidade, config.pais),
        "as cotações": lambda s: buscar_cotacoes(s, config.moedas),
        "as notícias": lambda s: buscar_noticias(s, config.feed_noticias, config.qtd_noticias),
        "o próximo feriado": lambda s: buscar_proximo_feriado(s, agora.date()),
    }

    briefing = Briefing(gerado_em=agora)
    inicio = time.perf_counter()

    # As chamadas são de rede (I/O), então threads reduzem o tempo total para o da fonte mais lenta.
    # Cada tarefa recebe sua própria sessão HTTP para não compartilhar estado entre threads.
    with ThreadPoolExecutor(max_workers=len(tarefas)) as executor:
        futuros = {nome: executor.submit(funcao, criar_sessao()) for nome, funcao in tarefas.items()}

    resultados = {}
    for nome, futuro in futuros.items():
        try:
            resultados[nome] = futuro.result()
        except Exception as erro:  # noqa: BLE001 — queremos registrar qualquer falha da fonte
            log.debug("Falha ao buscar %s", nome, exc_info=True)
            briefing.erros[nome] = descrever_erro(erro)

    briefing.clima = resultados.get("o clima")
    briefing.cotacoes = resultados.get("as cotações", [])
    briefing.noticias = resultados.get("as notícias", [])
    briefing.proximo_feriado = resultados.get("o próximo feriado")
    if briefing.clima:
        briefing.dicas = gerar_dicas(briefing.clima)

    log.info("Coleta concluída em %.2fs", time.perf_counter() - inicio)
    return briefing
