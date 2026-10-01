"""Previsão do tempo via API REST do Open-Meteo (gratuita, sem chave de acesso)."""

from __future__ import annotations

import requests

from .modelos import Clima

URL_GEOCODIFICACAO = "https://geocoding-api.open-meteo.com/v1/search"
URL_PREVISAO = "https://api.open-meteo.com/v1/forecast"

# Tradução dos códigos meteorológicos da WMO usados pelo Open-Meteo.
CODIGOS_WMO: dict[int, tuple[str, str]] = {
    0: ("Céu limpo", "☀️"),
    1: ("Predominantemente limpo", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Neblina", "🌫️"),
    48: ("Neblina com geada", "🌫️"),
    51: ("Garoa fraca", "🌦️"),
    53: ("Garoa moderada", "🌦️"),
    55: ("Garoa intensa", "🌦️"),
    56: ("Garoa congelante", "🌨️"),
    57: ("Garoa congelante intensa", "🌨️"),
    61: ("Chuva fraca", "🌧️"),
    63: ("Chuva moderada", "🌧️"),
    65: ("Chuva forte", "🌧️"),
    66: ("Chuva congelante", "🌨️"),
    67: ("Chuva congelante forte", "🌨️"),
    71: ("Neve fraca", "❄️"),
    73: ("Neve moderada", "❄️"),
    75: ("Neve forte", "❄️"),
    77: ("Grãos de neve", "❄️"),
    80: ("Pancadas de chuva fracas", "🌦️"),
    81: ("Pancadas de chuva", "🌧️"),
    82: ("Pancadas de chuva fortes", "⛈️"),
    85: ("Pancadas de neve", "🌨️"),
    86: ("Pancadas de neve fortes", "🌨️"),
    95: ("Trovoada", "⛈️"),
    96: ("Trovoada com granizo", "⛈️"),
    99: ("Trovoada com granizo forte", "⛈️"),
}


def localizar_cidade(sessao: requests.Session, cidade: str, pais: str | None = None) -> dict:
    """Converte o nome da cidade em latitude/longitude (geocodificação)."""
    parametros = {"name": cidade, "count": 1, "language": "pt", "format": "json"}
    if pais:
        parametros["countryCode"] = pais
    resposta = sessao.get(URL_GEOCODIFICACAO, params=parametros)
    resposta.raise_for_status()

    resultados = resposta.json().get("results")
    if not resultados:
        raise ValueError(f"Cidade '{cidade}' não encontrada.")
    return resultados[0]


def parse_previsao(dados: dict, local: dict) -> Clima:
    """Transforma o JSON do Open-Meteo em um objeto Clima."""
    atual = dados["current"]
    diario = dados["daily"]
    descricao, emoji = CODIGOS_WMO.get(atual["weather_code"], ("Condição desconhecida", "🌡️"))

    return Clima(
        cidade=local["name"],
        estado=local.get("admin1", ""),
        temperatura=atual["temperature_2m"],
        sensacao=atual["apparent_temperature"],
        umidade=atual["relative_humidity_2m"],
        vento_kmh=atual["wind_speed_10m"],
        descricao=descricao,
        emoji=emoji,
        maxima=diario["temperature_2m_max"][0],
        minima=diario["temperature_2m_min"][0],
        chance_chuva=diario["precipitation_probability_max"][0] or 0,
        indice_uv=diario["uv_index_max"][0] or 0,
        # Os horários chegam como "2026-10-01T05:45"; mantemos só "05:45".
        nascer_sol=diario["sunrise"][0][-5:],
        por_sol=diario["sunset"][0][-5:],
    )


def buscar_clima(sessao: requests.Session, cidade: str, pais: str | None = None) -> Clima:
    local = localizar_cidade(sessao, cidade, pais)
    parametros = {
        "latitude": local["latitude"],
        "longitude": local["longitude"],
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max,sunrise,sunset",
        "timezone": "auto",
        "forecast_days": 1,
    }
    resposta = sessao.get(URL_PREVISAO, params=parametros)
    resposta.raise_for_status()
    return parse_previsao(resposta.json(), local)


def gerar_dicas(clima: Clima) -> list[str]:
    """Regras simples que transformam números da previsão em recomendações práticas."""
    dicas = []
    if clima.chance_chuva >= 60:
        dicas.append(f"☂️ Leve guarda-chuva: {clima.chance_chuva}% de chance de chuva.")
    elif clima.chance_chuva >= 30:
        dicas.append(f"🌂 Talvez chova ({clima.chance_chuva}%). Um guarda-chuva na mochila não faz mal.")
    if clima.indice_uv >= 8:
        dicas.append(f"🧴 UV muito alto ({clima.indice_uv:.0f}): use protetor solar e evite sol entre 10h e 16h.")
    elif clima.indice_uv >= 6:
        dicas.append(f"🧴 UV alto ({clima.indice_uv:.0f}): passe protetor solar.")
    if clima.minima <= 12:
        dicas.append(f"🧥 Frio: a mínima chega a {clima.minima:.0f}°C. Leve um casaco.")
    elif clima.maxima - clima.minima >= 10:
        dicas.append(
            f"🧣 Grande variação térmica ({clima.minima:.0f}°C → {clima.maxima:.0f}°C): vista-se em camadas."
        )
    if clima.maxima >= 30:
        dicas.append(f"💧 Calor de {clima.maxima:.0f}°C: hidrate-se ao longo do dia.")
    if clima.vento_kmh >= 40:
        dicas.append(f"💨 Ventania ({clima.vento_kmh:.0f} km/h): cuidado com objetos soltos.")
    if not dicas:
        dicas.append("😎 Tempo tranquilo hoje. Aproveite o dia!")
    return dicas
