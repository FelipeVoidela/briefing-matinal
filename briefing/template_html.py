"""Template Jinja2 da página HTML do briefing.

Fica em um módulo Python (e não em um arquivo .html) para que o projeto seja 100% Python;
o Jinja2 preenche as variáveis e o filtro de escape protege contra HTML vindo das fontes externas.
"""

TEMPLATE_HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Briefing {{ b.gerado_em.strftime('%d/%m/%Y') }}</title>
  <style>
    :root {
      --fundo: #f4f1ea; --cartao: #ffffff; --texto: #1f2328; --suave: #6b6f76;
      --borda: #e4e0d6; --destaque: #c2410c; --alta: #15803d; --baixa: #b91c1c;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --fundo: #16181c; --cartao: #1f2228; --texto: #e8e6e3; --suave: #9aa0a6;
        --borda: #2f333a; --destaque: #fb923c; --alta: #4ade80; --baixa: #f87171;
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding: 32px 16px; background: var(--fundo); color: var(--texto);
      font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    }
    main { max-width: 880px; margin: 0 auto; display: grid; gap: 16px; }
    header h1 { margin: 0; font-size: 28px; }
    header p { margin: 4px 0 0; color: var(--suave); }
    section {
      background: var(--cartao); border: 1px solid var(--borda); border-radius: 14px; padding: 20px;
    }
    h2 { margin: 0 0 12px; font-size: 14px; text-transform: uppercase; letter-spacing: .06em; color: var(--suave); }
    .grade { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
    .temp { font-size: 52px; font-weight: 700; line-height: 1; }
    .cond { font-size: 18px; margin-top: 6px; }
    .detalhes { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 16px; color: var(--suave); font-size: 14px; }
    .detalhes b { color: var(--texto); font-weight: 600; }
    ul.dicas { margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; }
    table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
    th, td { padding: 10px 6px; text-align: right; border-bottom: 1px solid var(--borda); }
    th:first-child, td:first-child { text-align: left; }
    td:not(:first-child) { white-space: nowrap; }  /* não separar "R$" do valor nem "▲" do percentual */
    th { font-size: 13px; color: var(--suave); font-weight: 500; }
    tr:last-child td { border-bottom: 0; }
    .alta { color: var(--alta); } .baixa { color: var(--baixa); }
    ol.noticias { margin: 0; padding-left: 20px; display: grid; gap: 12px; }
    ol.noticias a { color: var(--texto); font-weight: 600; text-decoration: none; }
    ol.noticias a:hover { color: var(--destaque); text-decoration: underline; }
    ol.noticias p { margin: 2px 0 0; color: var(--suave); font-size: 14px; }
    .feriado { font-size: 18px; }
    .feriado strong { color: var(--destaque); }
    .aviso { color: var(--destaque); font-size: 14px; }
    footer { color: var(--suave); font-size: 13px; text-align: center; }
    @media (max-width: 520px) { .temp { font-size: 40px; } th:nth-child(4), td:nth-child(4) { display: none; } }
  </style>
</head>
<body>
<main>
  <header>
    <h1>{{ b.saudacao }}! ☕</h1>
    <p>Briefing gerado em {{ b.gerado_em.strftime('%d/%m/%Y às %H:%M') }}</p>
  </header>

  {% if b.clima %}{% set c = b.clima %}
  <div class="grade">
    <section>
      <h2>Clima em {{ c.cidade }}{% if c.estado %} - {{ c.estado }}{% endif %}</h2>
      <div class="temp">{{ c.emoji }} {{ c.temperatura | round | int }}°C</div>
      <div class="cond">{{ c.descricao }} · sensação {{ c.sensacao | round | int }}°C</div>
    </section>
    <section>
      <h2>Hoje</h2>
      <div class="detalhes">
        <span>Máxima <b>{{ c.maxima | round | int }}°C</b></span>
        <span>Mínima <b>{{ c.minima | round | int }}°C</b></span>
        <span>Chuva <b>{{ c.chance_chuva }}%</b></span>
        <span>Umidade <b>{{ c.umidade }}%</b></span>
        <span>Vento <b>{{ c.vento_kmh | round | int }} km/h</b></span>
        <span>Índice UV <b>{{ c.indice_uv | round | int }}</b></span>
        <span>Nascer do sol <b>{{ c.nascer_sol }}</b></span>
        <span>Pôr do sol <b>{{ c.por_sol }}</b></span>
      </div>
    </section>
  </div>
  {% endif %}

  {% if b.dicas %}
  <section>
    <h2>Dicas do dia</h2>
    <ul class="dicas">{% for d in b.dicas %}<li>{{ d }}</li>{% endfor %}</ul>
  </section>
  {% endif %}

  {% if b.cotacoes %}
  <section>
    <h2>Câmbio</h2>
    <table>
      <thead><tr><th>Moeda</th><th>Cotação</th><th>Variação</th><th>Mín / Máx</th></tr></thead>
      <tbody>
      {% for cot in b.cotacoes %}
        <tr>
          <td>{{ cot.nome }} <small>({{ cot.codigo }})</small></td>
          <td>{{ cot.valor | moeda }}</td>
          {% set classe = 'alta' if cot.variacao_pct > 0 else 'baixa' if cot.variacao_pct < 0 else '' %}
          <td class="{{ classe }}">{{ cot.variacao_pct | variacao }}</td>
          <td>
            {%- if cot.maxima is not none %}{{ cot.minima | moeda }} / {{ cot.maxima | moeda }}{% else %}—{% endif -%}
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% set fontes = b.cotacoes | map(attribute='fonte') | reject('equalto', 'AwesomeAPI') | unique | list %}
    {% if fontes %}<p class="aviso">Fonte principal indisponível; cotações de: {{ fontes | join(', ') }}.</p>{% endif %}
  </section>
  {% endif %}

  {% if b.noticias %}
  <section>
    <h2>Manchetes</h2>
    <ol class="noticias">
    {% for n in b.noticias %}
      <li>
        <a href="{{ n.link }}" target="_blank" rel="noopener">{{ n.titulo }}</a>
        {% if n.resumo %}<p>{{ n.resumo }}</p>{% endif %}
      </li>
    {% endfor %}
    </ol>
  </section>
  {% endif %}

  {% if b.proximo_feriado %}{% set f = b.proximo_feriado %}
  <section>
    <h2>Próximo feriado</h2>
    <div class="feriado">
      🎉 <strong>{{ f.nome }}</strong> · {{ f.data.strftime('%d/%m') }} ({{ f.dia_semana }})
      · {{ f.dias_restantes | contagem }}
    </div>
  </section>
  {% endif %}

  {% for fonte, erro in b.erros.items() %}
  <p class="aviso">⚠ Não foi possível obter {{ fonte }}: {{ erro }}</p>
  {% endfor %}

  <footer>Fontes: Open-Meteo · AwesomeAPI · g1 (RSS) · BrasilAPI</footer>
</main>
</body>
</html>
'''
