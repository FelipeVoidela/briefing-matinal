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
from datetime import datetime

import schedule
from rich.console import Console

from briefing.coleta import coletar_briefing
from briefing.config import Configuracao, carregar_configuracao, inteiro_positivo, separar_moedas
from briefing.notificador import enviar_telegram
from briefing.rede import criar_sessao, descrever_erro
from briefing.relatorio import exibir_no_terminal, gerar_html, gerar_texto_telegram

console = Console()


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
            console.print(f"[red]Falha ao enviar para o Telegram: {descrever_erro(erro)}[/red]")


def _execucao_agendada(config: Configuracao, args: argparse.Namespace) -> None:
    # Um erro inesperado em um dia não pode derrubar o agendamento dos dias seguintes.
    try:
        executar(config, args)
    except Exception:  # noqa: BLE001
        console.print_exception()
        console.print("[red]A execução falhou, mas o agendamento continua ativo.[/red]")


def agendar(horario: str, config: Configuracao, args: argparse.Namespace) -> None:
    schedule.every().day.at(horario).do(_execucao_agendada, config, args)
    console.print(f"⏰ Briefing agendado para todos os dias às [bold]{horario}[/bold]. Ctrl+C para sair.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\nAgendamento encerrado. Até amanhã! 👋")


def _argumento(conversor):
    """Adapta um validador para o argparse, que mostra a mensagem de erro em vez de um traceback."""
    def converter(valor: str):
        try:
            return conversor(valor)
        except ValueError as erro:
            raise argparse.ArgumentTypeError(str(erro)) from None
    converter.__name__ = conversor.__name__
    return converter


def validar_horario(valor: str) -> str:
    """Aceita "7:00" ou "07:00" e devolve sempre no formato HH:MM exigido pelo schedule."""
    try:
        return datetime.strptime(valor.strip(), "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ValueError(f"horário inválido '{valor}'. Use o formato HH:MM, ex.: 07:00.") from None


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera um briefing diário com clima, câmbio, notícias e feriados.")
    parser.add_argument("--cidade", help="cidade para a previsão do tempo (padrão: valor do .env ou São Paulo)")
    parser.add_argument("--moedas", type=_argumento(separar_moedas),
                        help="pares de moedas separados por vírgula, ex.: USD-BRL,EUR-BRL")
    parser.add_argument("--noticias", type=_argumento(inteiro_positivo), metavar="N", help="quantidade de manchetes")
    parser.add_argument("--html", action="store_true", help="salva o briefing como página HTML em saida/")
    parser.add_argument("--abrir", action="store_true", help="gera a página HTML e abre no navegador")
    parser.add_argument("--telegram", action="store_true", help="envia o briefing para o Telegram")
    parser.add_argument("--agendar", type=_argumento(validar_horario), metavar="HH:MM",
                        help="executa todos os dias no horário informado")
    parser.add_argument("-v", "--verbose", action="store_true", help="mostra logs detalhados")
    return parser


def main() -> None:
    # Garante que emojis e acentos apareçam corretamente no console do Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = criar_parser()
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    # Argumentos da linha de comando têm prioridade sobre o .env.
    try:
        config = carregar_configuracao()
    except ValueError as erro:
        parser.error(str(erro))
    if args.cidade:
        config.cidade = args.cidade
    if args.moedas:
        config.moedas = args.moedas
    if args.noticias is not None:
        config.qtd_noticias = args.noticias

    if args.agendar:
        agendar(args.agendar, config, args)
    else:
        executar(config, args)


if __name__ == "__main__":
    main()
