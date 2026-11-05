from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..busca import buscar_prestadores
from ..db import get_db
from ..security import destino_seguro, roles_required

bp = Blueprint("favoritos", __name__, url_prefix="/favoritos")


@bp.get("")
@roles_required("contratante")
def listar():
    db = get_db()
    ids = [r["prestador_id"] for r in db.consultar(
        "SELECT prestador_id FROM favoritos WHERE contratante_id = %s ORDER BY criado_em DESC", (g.user["id"],))]
    resultados, _ = buscar_prestadores({"ordem": "nota"}, ids=ids)
    return render_template("favoritos.html", resultados=resultados, salvos=set(ids))


@bp.post("/<int:uid>/alternar")
@roles_required("contratante")
def alternar(uid):
    db = get_db()
    if not db.um("SELECT usuario_id FROM prestadores WHERE usuario_id = %s", (uid,)):
        abort(404)
    existe = db.um("SELECT 1 AS x FROM favoritos WHERE contratante_id = %s AND prestador_id = %s",
                   (g.user["id"], uid))
    if existe:
        db.executar("DELETE FROM favoritos WHERE contratante_id = %s AND prestador_id = %s", (g.user["id"], uid))
        flash("Profissional removido dos salvos.", "sucesso")
    else:
        db.executar("INSERT INTO favoritos (contratante_id, prestador_id) VALUES (%s, %s)", (g.user["id"], uid))
        flash("Profissional salvo! Veja em “Salvos”.", "sucesso")
    return redirect(destino_seguro(request.form.get("next"), url_for("favoritos.listar")))
