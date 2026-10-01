# Roteiro do vídeo de demonstração (~4 min)

> Dica de gravação: use o **Xbox Game Bar** (`Win + Alt + R`) ou o **OBS Studio** e grave em tela cheia com o
> microfone ligado. Antes de começar, abra o VS Code com o projeto, um terminal com a `.venv` ativada e, se for
> mostrar o Telegram, o app/Telegram Web logado. Publique no YouTube como **Não listado**.

---

## 1. Apresentação e problema — 0:00 a 0:40

**Tela:** README aberto no VS Code (ou no GitHub).

> “Olá! Este é o **Briefing Matinal**, uma automação em Python que resolve um problema do dia a dia: toda manhã
> eu abria vários sites diferentes para ver a previsão do tempo, a cotação do dólar, as notícias e saber quando é o
> próximo feriado. Isso leva vários minutos e muitas abas. A ideia aqui é juntar tudo em um único comando, que
> ainda interpreta os dados e me dá dicas práticas, como levar guarda-chuva ou passar protetor solar.”

## 2. Tecnologias — 0:40 a 1:20

**Tela:** tabela de tecnologias do README e o `requirements.txt`.

> “O projeto integra quatro fontes externas. Três são **APIs REST** consumidas com a biblioteca `requests`:
> o Open-Meteo para o clima, a AwesomeAPI para o câmbio e a BrasilAPI para os feriados. As notícias vêm do feed do
> g1, que eu leio com **BeautifulSoup**, fazendo o *scraping* do XML e limpando o HTML dos resumos. Por fim, o
> briefing pode ser enviado para o **Telegram** através de um `POST` na API de bots. Uso também o `rich` para a
> interface no terminal, o `Jinja2` para gerar a página HTML e o `schedule` para rodar todo dia no mesmo horário.
> Todas as dependências estão no `requirements.txt`.”

## 3. Lógica do código — 1:20 a 2:40

**Tela:** navegue pelos arquivos enquanto fala.

1. **`main.py` → `coletar_briefing`**
   > “O coração do programa é esta função. Ela dispara as quatro consultas **em paralelo** com um
   > `ThreadPoolExecutor`, então o tempo total é o da API mais lenta, não a soma de todas. Se uma fonte falhar,
   > o erro é registrado e o resto do briefing continua sendo gerado.”
2. **`briefing/rede.py`**
   > “Todas as requisições usam uma sessão com timeout padrão e até três retentativas automáticas com espera
   > exponencial, para lidar com instabilidades das APIs.”
3. **`briefing/clima.py`** → `buscar_clima` e `gerar_dicas`
   > “Aqui eu primeiro converto o nome da cidade em latitude e longitude, depois busco a previsão. Os códigos
   > meteorológicos são traduzidos para português com emoji, e a função `gerar_dicas` transforma os números em
   > recomendações: chance de chuva alta vira ‘leve guarda-chuva’, UV alto vira ‘passe protetor’, e assim por diante.”
4. **`briefing/noticias.py`**
   > “Nas notícias, o BeautifulSoup percorre os itens do RSS, extrai título, link e data, e limpa as tags HTML da
   > descrição para montar um resumo curto.”
5. **`briefing/relatorio.py`** (rapidamente)
   > “O mesmo objeto `Briefing` é apresentado de três formas: no terminal, em HTML e como mensagem do Telegram.”

## 4. Demonstração ao vivo — 2:40 a 4:10

**Tela:** terminal.

1. `python main.py`
   > “Rodando o comando básico… em poucos segundos aparece o clima de São Paulo com as dicas do dia, a tabela de
   > câmbio com a variação em verde ou vermelho, as manchetes e a contagem para o próximo feriado.”
2. `python main.py --cidade "Porto Alegre" --abrir`
   > “Posso trocar a cidade pela linha de comando. Com `--abrir`, ele também gera esta página HTML e abre no
   > navegador. Ela funciona no celular e no modo escuro.”
3. `python main.py --cidade Cidadequenaoexiste`
   > “E se algo der errado? Aqui informei uma cidade que não existe: o programa avisa que não conseguiu o clima,
   > mas entrega todo o resto normalmente.”
4. *(se configurou o Telegram)* `python main.py --telegram`
   > “E com `--telegram` o briefing chega direto no meu celular.” → mostre a mensagem chegando.
5. `python main.py --agendar 07:00 --telegram` (mostre a mensagem de agendamento e encerre com Ctrl+C)
   > “Para automatizar de verdade, basta agendar: todo dia às sete da manhã eu recebo o resumo sem fazer nada.”
6. *(opcional)* `python -m pytest -q`
   > “O projeto também tem testes automatizados que validam a lógica sem depender da internet.”

## 5. Encerramento — 4:10 a 4:30

> “Então é isso: o Briefing Matinal transforma vários minutos de pesquisa em um único comando ou em uma mensagem
> automática. O código está no GitHub, com instruções no README. Obrigado!”
