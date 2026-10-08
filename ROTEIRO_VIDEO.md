# Roteiro do vídeo de demonstração (~4min30)

> **Antes de gravar**
> - Grave com o **Xbox Game Bar** (`Win + Alt + R`) ou o **OBS Studio**, em tela cheia e com o microfone ligado.
> - Deixe abertos: o VS Code com o projeto, um terminal na pasta do projeto e, no navegador, o app
>   **https://briefing-matinal.streamlit.app** e o repositório no GitHub.
> - Abra o app uma vez antes de gravar: se ele estiver "dormindo" (Streamlit desliga apps parados), leva uns
>   segundos para acordar e você não perde tempo no vídeo.
> - Publique no YouTube como **Não listado**.
>
> O texto narrado tem ~600 palavras (≈ 4 min em ritmo natural). Os trechos marcados como *(opcional)* podem ser
> cortados se o vídeo passar de 5 minutos.

---

## 1. O problema — 0:00 a 0:30

**Tela:** README do projeto no GitHub.

> “Olá! Este é o **Briefing Matinal**, uma automação em Python que resolve um problema do dia a dia: toda manhã
> eu abria vários sites para ver a previsão do tempo, a cotação do dólar, as notícias e quando é o próximo feriado.
> A ideia é juntar tudo em um único lugar, em poucos segundos, e ainda interpretar os dados, por exemplo:
> ‘vai chover, leve guarda-chuva’. O projeto tem duas versões: uma de linha de comando e uma versão web.”

## 2. Tecnologias — 0:30 a 1:10

**Tela:** tabela “Tecnologias e integrações” do README e depois o `requirements.txt`.

> “O projeto é 100% Python e integra várias fontes externas. As **APIs REST** são consumidas com a biblioteca
> `requests`: o Open-Meteo para o clima, a AwesomeAPI para o câmbio e a BrasilAPI para os feriados. As notícias vêm
> do feed do g1, que eu leio com **BeautifulSoup**, fazendo *web scraping*. O briefing também pode ser enviado para o
> **Telegram** por um `POST` na API de bots. A versão web foi feita com **Streamlit** e está publicada no Streamlit
> Community Cloud. Todas as dependências estão no `requirements.txt`.”

## 3. Lógica do código — 1:10 a 2:30

**Tela:** navegue pelos arquivos no VS Code enquanto fala.

1. **`briefing/coleta.py` → `coletar_briefing`**
   > “O coração do projeto é esta função, usada pelas duas versões. Ela consulta as quatro fontes **em paralelo**
   > com um `ThreadPoolExecutor`, então o tempo total é o da API mais lenta, não a soma de todas. Se uma fonte
   > falhar, o erro é registrado e o resto do briefing continua sendo gerado.”
2. **`briefing/clima.py` → `gerar_dicas`**
   > “Aqui os números da previsão viram recomendações: chance alta de chuva vira ‘leve guarda-chuva’, índice UV
   > alto vira ‘passe protetor solar’, e assim por diante.”
3. **`briefing/noticias.py`**
   > “Nas notícias, o BeautifulSoup percorre o RSS, extrai título, link e data, limpa o HTML dos resumos e ignora
   > matérias repetidas.”
4. **`briefing/cambio.py` → `buscar_cotacoes`**
   > “No câmbio eu tive um problema real ao publicar na nuvem: a AwesomeAPI bloqueia os servidores do Streamlit por
   > excesso de requisições. Então criei **fontes reserva**: se a principal falhar, o programa busca as moedas no
   > Banco Central Europeu e as criptomoedas no CoinGecko, e avisa de onde vieram os dados.”
5. **`main.py` e `streamlit_app.py`** (rapidamente, um ao lado do outro)
   > “Por fim, a mesma lógica tem duas interfaces: o `main.py` monta a versão de terminal, com Telegram e
   > agendamento, e o `streamlit_app.py` monta a versão web.”

## 4. Demonstração no terminal — 2:30 a 3:20

**Tela:** terminal.

1. `python main.py`
   > “Rodando o comando básico… em poucos segundos aparecem o clima com as dicas do dia, o câmbio com a variação em
   > verde ou vermelho, as manchetes e a contagem para o próximo feriado.”
2. `python main.py --cidade "Porto Alegre" --abrir`
   > “Posso trocar a cidade e, com `--abrir`, ele gera uma página HTML e abre no navegador.”
3. `python main.py --agendar 07:00` (mostre a mensagem e encerre com `Ctrl+C`)
   > “E para automatizar de verdade, basta agendar: todo dia às sete da manhã o briefing é gerado, e com
   > `--telegram` ele chega direto no celular.”
4. *(opcional)* `python main.py --noticias 0`
   > “Entradas inválidas geram mensagens claras, sem quebrar o programa.”

## 5. Demonstração na web — 3:20 a 4:20

**Tela:** navegador em **https://briefing-matinal.streamlit.app**.

1. Mostre a página inicial.
   > “Esta é a versão web, publicada no Streamlit Community Cloud. Qualquer pessoa pode acessar pelo link, sem
   > instalar nada. O horário segue o fuso de Brasília, mesmo o servidor estando em outro fuso.”
2. Na barra lateral, troque a **cidade** (ex.: “Recife”) e adicione uma **moeda** (ex.: Libra).
   > “Na barra lateral eu escolho a cidade, as moedas e quantas manchetes quero ver, e o briefing se atualiza na
   > hora. Os resultados ficam em cache por dez minutos, para não sobrecarregar as APIs.”
3. Role até o câmbio e mostre a legenda das fontes (se ela aparecer).
   > “Aqui dá para ver a fonte reserva em ação: o app avisa que as cotações vieram do Banco Central Europeu e do
   > CoinGecko.”
4. Clique em **Baixar briefing em HTML**.
   > “E posso baixar o briefing como uma página HTML para guardar ou compartilhar.”
5. *(opcional)* Digite uma cidade que não existe.
   > “Se algo falhar, o app avisa e mostra todo o resto normalmente.”

## 6. Encerramento — 4:20 a 4:40

**Tela:** README no GitHub (botão “Abrir no Streamlit” visível).

> “Então é isso: o Briefing Matinal transforma vários minutos de pesquisa em um comando, uma mensagem automática
> ou um link na web. O código está no GitHub, com testes automatizados e instruções no README. Obrigado!”
