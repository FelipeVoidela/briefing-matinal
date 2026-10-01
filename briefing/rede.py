"""Sessão HTTP com timeout padrão e retentativas automáticas para falhas temporárias."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT_SEGUNDOS = 10


class _SessaoComTimeout(requests.Session):
    """requests não tem timeout padrão — sem isso, uma API travada congelaria o bot."""

    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT_SEGUNDOS)
        return super().request(*args, **kwargs)


def criar_sessao() -> requests.Session:
    sessao = _SessaoComTimeout()

    # Até 3 novas tentativas com espera exponencial (0,5s, 1s, 2s) em erros transitórios.
    retentativas = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    adaptador = HTTPAdapter(max_retries=retentativas)
    sessao.mount("https://", adaptador)
    sessao.mount("http://", adaptador)
    sessao.headers["User-Agent"] = "BriefingMatinal/1.0 (projeto academico)"
    return sessao
