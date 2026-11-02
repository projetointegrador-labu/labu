from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..security import login_required, roles_required

bp = Blueprint("servicos", __name__, url_prefix="/servicos")

# transições permitidas: {perfil: {status_atual: {novos}}}
TRANSICOES = {
    "prestador": {"solicitado": {"aceito", "recusado"}, "aceito": {"concluido"}},
    "contratante": {"solicitado": {"cancelado"}, "aceito": {"cancelado"}},
}


@bp.get("")
@login_required
def listar():
    db = get_db()
    if g.user["perfil"] == "admin":
        return redirect(url_for("admin.dashboard"))
    campo = "prestador_id" if g.user["perfil"] == "prestador" else "contratante_id"
    outro = "contratante_id" if campo == "prestador_id" else "prestador_id"
    itens = db.consultar(
        f"""SELECT s.*, c.nome AS categoria, o.nome AS outra_parte
            FROM servicos s JOIN categorias c ON c.id = s.categoria_id
            JOIN usuarios o ON o.id = s.{outro}
            WHERE s.{campo} = %s ORDER BY s.criado_em DESC, s.id DESC""",
        (g.user["id"],),
    )
    return render_template("servicos.html", itens=itens)


@bp.route("/novo/<int:prestador_id>", methods=["GET", "POST"])
@roles_required("contratante")
def novo(prestador_id):
    db = get_db()
    p = db.um(
        """SELECT u.id, u.nome, p.categoria_id, c.nome AS categoria
           FROM prestadores p JOIN usuarios u ON u.id = p.usuario_id
           JOIN categorias c ON c.id = p.categoria_id
           WHERE u.id = %s AND p.visivel = 1 AND u.ativo = 1""",
        (prestador_id,),
    )
    if not p:
        abort(404)
    erros, form = {}, {}
    if request.method == "POST":
        form = {"descricao": (request.form.get("descricao") or "").strip(),
                "data_prevista": (request.form.get("data_prevista") or "").strip()}
        if len(form["descricao"]) < 10:
            erros["descricao"] = "Descreva o serviço (mínimo de 10 caracteres)."
        elif len(form["descricao"]) > 1000:
            erros["descricao"] = "Use no máximo 1000 caracteres."
        data = None
        if form["data_prevista"]:
            try:
                data = date.fromisoformat(form["data_prevista"])
                if data < date.today():
                    erros["data_prevista"] = "A data não pode estar no passado."
            except ValueError:
                erros["data_prevista"] = "Data inválida."
        if not erros:
            db.executar(
                """INSERT INTO servicos (prestador_id, contratante_id, categoria_id, descricao, data_prevista)
                   VALUES (%s, %s, %s, %s, %s)""",
                (p["id"], g.user["id"], p["categoria_id"], form["descricao"],
                 data.isoformat() if data else None),
            )
            flash("Solicitação enviada! Acompanhe o status no seu histórico.", "sucesso")
            return redirect(url_for("servicos.listar"))
    return render_template("servico_form.html", p=p, erros=erros, form=form, hoje=date.today().isoformat())


@bp.post("/<int:sid>/status")
@login_required
def status(sid):
    db = get_db()
    s = db.um("SELECT * FROM servicos WHERE id = %s", (sid,))
    if not s:
        abort(404)
    perfil = g.user["perfil"]
    if perfil == "prestador" and s["prestador_id"] != g.user["id"]:
        abort(403)
    if perfil == "contratante" and s["contratante_id"] != g.user["id"]:
        abort(403)
    novo_status = request.form.get("status", "")
    if novo_status not in TRANSICOES.get(perfil, {}).get(s["status"], set()):
        flash("Esta alteração de status não é permitida.", "erro")
        return redirect(url_for("servicos.listar"))
    if novo_status == "concluido":
        db.executar("UPDATE servicos SET status=%s, concluido_em=CURRENT_TIMESTAMP WHERE id=%s", (novo_status, sid))
    else:
        db.executar("UPDATE servicos SET status=%s WHERE id=%s", (novo_status, sid))
    flash("Status atualizado.", "sucesso")
    return redirect(url_for("servicos.listar"))


@bp.post("/<int:sid>/avaliar")
@roles_required("contratante")
def avaliar(sid):
    db = get_db()
    s = db.um("SELECT * FROM servicos WHERE id = %s AND contratante_id = %s", (sid, g.user["id"]))
    if not s:
        abort(404)
    try:
        nota = int(request.form.get("nota", ""))
    except ValueError:
        nota = 0
    if s["status"] != "concluido" or s["avaliacao"] is not None:
        flash("Este serviço não pode ser avaliado.", "erro")
    elif not 1 <= nota <= 5:
        flash("Escolha uma nota de 1 a 5.", "erro")
    else:
        comentario = (request.form.get("comentario") or "").strip()[:500] or None
        db.executar("UPDATE servicos SET avaliacao=%s, comentario=%s WHERE id=%s", (nota, comentario, sid))
        flash("Obrigado pela avaliação!", "sucesso")
    return redirect(url_for("servicos.listar"))
