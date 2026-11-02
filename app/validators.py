"""Validações de entrada."""
import re

from .seed import ESTADOS

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def email_valido(email: str) -> bool:
    return bool(email) and len(email) <= 190 and bool(_EMAIL.match(email))


def telefone_valido(tel: str) -> bool:
    return len(so_digitos(tel)) in (10, 11)


def cep_valido(cep: str) -> bool:
    return len(so_digitos(cep)) == 8


def uf_valida(uf: str) -> bool:
    return (uf or "").upper() in ESTADOS


def senha_forte(senha: str):
    """Retorna mensagem de erro ou None."""
    if len(senha or "") < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        return "A senha deve conter letras e números."
    return None


def numero(valor, minimo, maximo, padrao=None):
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return padrao
    return n if minimo <= n <= maximo else padrao


def coordenada(valor, minimo, maximo):
    try:
        n = float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return n if minimo <= n <= maximo else None
