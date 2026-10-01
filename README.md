# ☕ Briefing Matinal

Automação em Python que monta, com **um único comando**, o resumo do seu dia:
previsão do tempo com dicas práticas, cotações de moedas, principais manchetes e contagem para o próximo feriado.
O resultado aparece no terminal, pode ser salvo como página HTML e enviado para o seu Telegram — inclusive de forma
agendada, todo dia no mesmo horário.

## O problema

Toda manhã a gente abre 4 ou 5 sites/apps diferentes para saber se vai chover, quanto está o dólar, o que está
acontecendo no mundo e quando é o próximo feriado. São vários minutos e muitas abas por dia. O Briefing Matinal
junta tudo em um só lugar em poucos segundos, e ainda **interpreta** os dados (ex.: “96% de chance de chuva → leve
guarda-chuva”).

## Tecnologias e integrações

| Fonte / Lib | Tipo de integração | Uso |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | API REST (`requests`) | geocodificação da cidade + previsão do tempo |
| [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas) | API REST (`requests`) | cotações de dólar, euro, bitcoin… |
| [BrasilAPI](https://brasilapi.com.br/) | API REST (`requests`) | feriados nacionais |
| [g1 RSS](https://g1.globo.com/rss/g1/) | Web scraping (`BeautifulSoup` + `lxml`) | manchetes e resumos |
| [Telegram Bot API](https://core.telegram.org/bots/api) | API REST, envio via `POST` | entrega do briefing no celular (opcional) |
| `rich` | — | interface colorida no terminal |
| `Jinja2` | — | template da página HTML |
| `schedule` | — | execução diária agendada |
| `python-dotenv` | — | configuração via `.env` |

Nenhuma das APIs exige cadastro ou chave: o projeto funciona assim que é clonado.

## Como executar

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python main.py
```

### Opções

```bash
python main.py --cidade "Rio de Janeiro"    # outra cidade
python main.py --moedas USD-BRL,GBP-BRL     # outras moedas
python main.py --noticias 8                 # quantidade de manchetes
python main.py --html                       # salva a página em saida/
python main.py --abrir                      # salva e abre a página no navegador
python main.py --telegram                   # envia para o Telegram
python main.py --agendar 07:00 --telegram   # todo dia às 07:00
python main.py -v                           # logs detalhados (mostra as requisições HTTP)
```

Para configurar valores padrão, copie `.env.example` para `.env` e edite.

### Telegram (opcional)

1. No Telegram, fale com o **@BotFather**, envie `/newbot` e copie o token.
2. Mande qualquer mensagem para o seu bot e acesse `https://api.telegram.org/bot<TOKEN>/getUpdates`
   para descobrir o seu `chat.id`.
3. Preencha `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` no `.env` e rode `python main.py --telegram`.

## Arquitetura

```
main.py                 CLI (argparse), coleta paralela, agendamento
briefing/
├── config.py           leitura do .env com valores padrão
├── rede.py             sessão HTTP com timeout e retentativas (backoff exponencial)
├── clima.py            Open-Meteo + regras que geram as "dicas do dia"
├── cambio.py           AwesomeAPI
├── noticias.py         scraping do RSS com BeautifulSoup
├── feriados.py         BrasilAPI
├── notificador.py      envio via Telegram Bot API
├── relatorio.py        saída no terminal (rich), HTML (Jinja2) e texto do Telegram
├── formatacao.py       números e moedas no padrão brasileiro
├── modelos.py          dataclasses compartilhadas
└── templates/briefing.html
tests/                  testes unitários (sem acesso à rede)
```

Decisões técnicas:

- **Coleta paralela** com `ThreadPoolExecutor`: as 4 fontes são consultadas ao mesmo tempo, então o tempo total
  é o da fonte mais lenta, e não a soma de todas.
- **Tolerância a falhas**: se uma fonte cair (ou a cidade não existir), o erro aparece como aviso e o restante do
  briefing continua sendo gerado.
- **Resiliência de rede**: timeout padrão e até 3 retentativas automáticas em erros `429/5xx`.
- **Separação entre busca e interpretação** (`buscar_*` × `parse_*`): a lógica pode ser testada com respostas de exemplo,
  sem internet.

## Testes

```bash
python -m pytest -q
```
