"""Funções de formatação no padrão brasileiro."""


def formatar_numero(valor: float, casas: int = 2) -> str:
    # 1234.5 -> "1.234,50"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_moeda(valor: float) -> str:
    # Valores pequenos (ex.: dólar) ganham 4 casas; grandes (ex.: bitcoin) ficam com 2.
    casas = 2 if valor >= 100 else 4
    return f"R$ {formatar_numero(valor, casas)}"


def formatar_variacao(pct: float) -> str:
    seta = "▲" if pct > 0 else "▼" if pct < 0 else "■"
    return f"{seta} {formatar_numero(abs(pct))}%"


def descrever_contagem(dias: int) -> str:
    if dias == 0:
        return "é hoje! 🎉"
    if dias == 1:
        return "é amanhã!"
    return f"faltam {dias} dias"
