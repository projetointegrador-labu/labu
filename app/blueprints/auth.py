from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db
from ..security import (
    bloqueado, destino_seguro, entrar as iniciar_sessao, limpar_falhas,
    login_required, registrar_falha, sair as encerrar_sessao,
)
from ..validators import email_valido, senha_forte, so_digitos, telefone_valido

bp = Blueprint("auth", __name__)

# hash fictício para igualar o tempo de resposta quando o e-mail não existe
_HASH_FALSO = generate_password_hash("senha-inexistente")


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if g.user:
        return redirect(url_for("main.index"))
    erros, form = {}, {}
    if request.method == "POST":
        form = {k: (request.form.get(k) or "").strip() for k in ("nome", "email", "telefone", "perfil")}
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar", "")
        form["email"] = form["email"].lower()

        if len(form["nome"]) < 3:
            erros["nome"] = "Informe seu nome completo."
        if not email_valido(form["email"]):
            erros["email"] = "Informe um e-mail válido."
        if form["telefone"] and not telefone_valido(form["telefone"]):
            erros["telefone"] = "Telefone inválido. Use DDD + número."
        if form["perfil"] not in ("contratante", "prestador"):
            erros["perfil"] = "Escolha o tipo de conta."
        msg = senha_forte(senha)
        if msg:
            erros["senha"] = msg
        elif senha != confirmar:
            erros["confirmar"] = "As senhas não conferem."
        if not request.form.get("consentimento"):
            erros["consentimento"] = "É necessário aceitar a Política de Privacidade (LGPD)."

        db = get_db()
        if "email" not in erros and db.um("SELECT id FROM usuarios WHERE email = %s", (form["email"],)):
            erros["email"] = "Este e-mail já está cadastrado."

        if not erros:
            uid = db.executar(
                """INSERT INTO usuarios (nome, email, senha_hash, telefone, perfil,
                                         consentimento_lgpd, consentimento_em)
                   VALUES (%s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP)""",
                (form["nome"], form["email"], generate_password_hash(senha),
                 so_digitos(form["telefone"]) or None, form["perfil"]),
            )
            iniciar_sessao(uid)
            if form["perfil"] == "prestador":
                flash("Conta criada! Complete seu perfil profissional para aparecer nas buscas.", "sucesso")
                return redirect(url_for("prestador.perfil"))
            flash("Conta criada com sucesso!", "sucesso")
            return redirect(url_for("main.index"))
    return render_template("cadastro.html", erros=erros, form=form)


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    if g.user:
        return redirect(url_for("main.index"))
    erro, email = None, ""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha", "")
        chave = f"{request.remote_addr}|{email}"
        espera = bloqueado(chave)
        if espera:
            erro = f"Muitas tentativas. Tente novamente em {espera // 60 + 1} minuto(s)."
        else:
            u = get_db().um("SELECT * FROM usuarios WHERE email = %s", (email,))
            ok = check_password_hash(u["senha_hash"] if u else _HASH_FALSO, senha)
            if u and ok and u["ativo"]:
                limpar_falhas(chave)
                iniciar_sessao(u["id"])
                if u["perfil"] == "admin":
                    return redirect(destino_seguro(request.args.get("next"), url_for("admin.dashboard")))
                return redirect(destino_seguro(request.args.get("next"), url_for("main.index")))
            registrar_falha(chave)
            erro = "E-mail ou senha incorretos." if not (u and ok) else "Conta desativada."
    return render_template("login.html", erro=erro, email=email)


@bp.post("/sair")
def sair():
    encerrar_sessao()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("main.index"))


@bp.route("/conta", methods=["GET", "POST"])
@login_required
def conta():
    erros = {}
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()
        if len(nome) < 3:
            erros["nome"] = "Informe seu nome completo."
        if telefone and not telefone_valido(telefone):
            erros["telefone"] = "Telefone inválido. Use DDD + número."
        nova = request.form.get("nova_senha", "")
        if nova:
            atual = get_db().um("SELECT senha_hash FROM usuarios WHERE id = %s", (g.user["id"],))
            if not check_password_hash(atual["senha_hash"], request.form.get("senha_atual", "")):
                erros["senha_atual"] = "Senha atual incorreta."
            msg = senha_forte(nova)
            if msg:
                erros["nova_senha"] = msg
        if not erros:
            db = get_db()
            db.executar(
                "UPDATE usuarios SET nome = %s, telefone = %s WHERE id = %s",
                (nome, so_digitos(telefone) or None, g.user["id"]),
            )
            if nova:
                db.executar("UPDATE usuarios SET senha_hash = %s WHERE id = %s",
                            (generate_password_hash(nova), g.user["id"]))
            flash("Dados atualizados.", "sucesso")
            return redirect(url_for("auth.conta"))
    return render_template("conta.html", erros=erros)


@bp.post("/conta/excluir")
@login_required
def excluir_conta():
    """Direito de eliminação dos dados (LGPD, art. 18, VI)."""
    db = get_db()
    u = db.um("SELECT senha_hash, perfil FROM usuarios WHERE id = %s", (g.user["id"],))
    if u["perfil"] == "admin":
        flash("Contas de administrador não podem ser excluídas por aqui.", "erro")
        return redirect(url_for("auth.conta"))
    if not check_password_hash(u["senha_hash"], request.form.get("senha", "")):
        flash("Senha incorreta. A conta não foi excluída.", "erro")
        return redirect(url_for("auth.conta"))
    db.executar("DELETE FROM usuarios WHERE id = %s", (g.user["id"],))
    encerrar_sessao()
    flash("Sua conta e seus dados foram excluídos.", "sucesso")
    return redirect(url_for("main.index"))
