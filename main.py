"""Briefing Matinal — ponto de entrada da linha de comando.

Exemplos:
    python main.py                         # briefing no terminal
    python main.py --cidade Recife --abrir # gera a página HTML e abre no navegador
    python main.py --telegram              # também envia para o Telegram
    python main.py --agendar 07:00         # roda todo dia às 07:00
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import schedule
from rich.console import Console

from briefing.cambio import buscar_cotacoes
from briefing.clima import buscar_clima, gerar_dicas
from briefing.config import Configuracao, carregar_configuracao
from briefing.feriados import buscar_proximo_feriado
from briefing.modelos import Briefing
from briefing.noticias import buscar_noticias
from briefing.notificador import enviar_telegram
from briefing.rede import criar_sessao
from briefing.relatorio import exibir_no_terminal, gerar_html, gerar_texto_telegram

console = Console()
log = logging.getLogger("briefing")


def coletar_briefing(config: Configuracao) -> Briefing:
    """Consulta todas as fontes em paralelo. Uma fonte com erro não derruba as demais."""
    tarefas = {
        "o clima": lambda s: buscar_clima(s, config.cidade, config.pais),
        "as cotações": lambda s: buscar_cotacoes(s, config.moedas),
        "as notícias": lambda s: buscar_noticias(s, config.feed_noticias, config.qtd_noticias),
        "o próximo feriado": lambda s: buscar_proximo_feriado(s),
    }

    briefing = Briefing(gerado_em=datetime.now())
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
            briefing.erros[nome] = str(erro)

    briefing.clima = resultados.get("o clima")
    briefing.cotacoes = resultados.get("as cotações", [])
    briefing.noticias = resultados.get("as notícias", [])
    briefing.proximo_feriado = resultados.get("o próximo feriado")
    if briefing.clima:
        briefing.dicas = gerar_dicas(briefing.clima)

    log.info("Coleta concluída em %.2fs", time.perf_counter() - inicio)
    return briefing


def executar(config: Configuracao, args: argparse.Namespace) -> None:
    with console.status("[cyan]Consultando APIs e lendo notícias...[/cyan]"):
        briefing = coletar_briefing(config)

    exibir_no_terminal(briefing, console)

    if args.html or args.abrir:
        caminho = gerar_html(briefing, config.pasta_saida)
        console.print(f"\n📄 Página salva em [bold]{caminho}[/bold]")
        if args.abrir:
            webbrowser.open(caminho.as_uri())

    if args.telegram:
        if not config.telegram_configurado:
            console.print("[red]Defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no arquivo .env para usar --telegram.[/red]")
            return
        try:
            enviar_telegram(criar_sessao(), config.telegram_token, config.telegram_chat_id,
                            gerar_texto_telegram(briefing))
            console.print("📨 Briefing enviado para o Telegram!")
        except Exception as erro:  # noqa: BLE001
            console.print(f"[red]Falha ao enviar para o Telegram: {erro}[/red]")


def agendar(horario: str, config: Configuracao, args: argparse.Namespace) -> None:
    schedule.every().day.at(horario).do(executar, config, args)
    console.print(f"⏰ Briefing agendado para todos os dias às [bold]{horario}[/bold]. Ctrl+C para sair.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\nAgendamento encerrado. Até amanhã! 👋")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera um briefing diário com clima, câmbio, notícias e feriados.")
    parser.add_argument("--cidade", help="cidade para a previsão do tempo (padrão: valor do .env ou São Paulo)")
    parser.add_argument("--moedas", help="pares de moedas separados por vírgula, ex.: USD-BRL,EUR-BRL")
    parser.add_argument("--noticias", type=int, metavar="N", help="quantidade de manchetes")
    parser.add_argument("--html", action="store_true", help="salva o briefing como página HTML em saida/")
    parser.add_argument("--abrir", action="store_true", help="gera a página HTML e abre no navegador")
    parser.add_argument("--telegram", action="store_true", help="envia o briefing para o Telegram")
    parser.add_argument("--agendar", metavar="HH:MM", help="executa todos os dias no horário informado")
    parser.add_argument("-v", "--verbose", action="store_true", help="mostra logs detalhados")
    return parser


def main() -> None:
    # Garante que emojis e acentos apareçam corretamente no console do Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = criar_parser().parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    # Argumentos da linha de comando têm prioridade sobre o .env.
    config = carregar_configuracao()
    if args.cidade:
        config.cidade = args.cidade
    if args.moedas:
        config.moedas = [m.strip().upper() for m in args.moedas.split(",")]
    if args.noticias:
        config.qtd_noticias = args.noticias

    if args.agendar:
        agendar(args.agendar, config, args)
    else:
        executar(config, args)


if __name__ == "__main__":
    main()
