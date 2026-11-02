"""Sessão, CSRF, autenticação e autorização."""
import hmac
import secrets
import time
from functools import wraps
from urllib.parse import urlparse

from flask import abort, flash, g, redirect, request, session, url_for

from .db import get_db

_TENTATIVAS = {}  # {chave: (contagem, bloqueado_ate)} - em memória (por processo)
MAX_TENTATIVAS = 5
BLOQUEIO_SEG = 300


def csrf_token() -> str:
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(32)
    return session["_csrf"]


def verificar_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        enviado = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        esperado = session.get("_csrf", "")
        if not esperado or not hmac.compare_digest(enviado, esperado):
            abort(400, description="Token de segurança inválido. Recarregue a página e tente novamente.")


def carregar_usuario():
    g.user = None
    uid = session.get("uid")
    if uid:
        user = get_db().um(
            "SELECT id, nome, email, telefone, perfil, ativo FROM usuarios WHERE id = %s", (uid,)
        )
        if user and user["ativo"]:
            g.user = user
        else:
            session.clear()


def entrar(usuario_id: int):
    session.clear()
    session["uid"] = usuario_id
    session.permanent = True
    csrf_token()


def sair():
    session.clear()


def login_required(view):
    @wraps(view)
    def wrapper(*a, **kw):
        if g.user is None:
            flash("Faça login para continuar.", "aviso")
            return redirect(url_for("auth.entrar", next=request.path))
        return view(*a, **kw)

    return wrapper


def roles_required(*perfis):
    def deco(view):
        @wraps(view)
        @login_required
        def wrapper(*a, **kw):
            if g.user["perfil"] not in perfis:
                abort(403)
            return view(*a, **kw)

        return wrapper

    return deco


def destino_seguro(destino, padrao):
    """Evita open redirect: aceita apenas caminhos relativos internos."""
    if destino:
        p = urlparse(destino)
        if not p.scheme and not p.netloc and destino.startswith("/") and not destino.startswith("//"):
            return destino
    return padrao


def bloqueado(chave) -> int:
    reg = _TENTATIVAS.get(chave)
    if reg and reg[1] > time.time():
        return int(reg[1] - time.time())
    return 0


def registrar_falha(chave):
    cont, _ = _TENTATIVAS.get(chave, (0, 0))
    cont += 1
    ate = time.time() + BLOQUEIO_SEG if cont >= MAX_TENTATIVAS else 0
    _TENTATIVAS[chave] = (0 if ate else cont, ate)


def limpar_falhas(chave):
    _TENTATIVAS.pop(chave, None)
