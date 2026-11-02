import csv
import io
from collections import Counter

from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..security import roles_required
from ..seed import STATUS_SERVICO

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _mes(valor):
    return str(valor)[:7] if valor else "—"


@bp.get("")
@roles_required("admin")
def dashboard():
    db = get_db()
    n = lambda sql: db.um(sql)["n"]  # noqa: E731
    totais = {
        "usuarios": n("SELECT COUNT(*) AS n FROM usuarios WHERE perfil <> 'admin'"),
        "prestadores": n("SELECT COUNT(*) AS n FROM prestadores"),
        "contratantes": n("SELECT COUNT(*) AS n FROM usuarios WHERE perfil = 'contratante'"),
        "servicos": n("SELECT COUNT(*) AS n FROM servicos"),
        "concluidos": n("SELECT COUNT(*) AS n FROM servicos WHERE status = 'concluido'"),
    }
    return render_template("admin/dashboard.html", totais=totais)


@bp.get("/usuarios")
@roles_required("admin")
def usuarios():
    lista = get_db().consultar(
        "SELECT id, nome, email, perfil, ativo, criado_em FROM usuarios ORDER BY criado_em DESC, id DESC LIMIT 500"
    )
    return render_template("admin/usuarios.html", usuarios=lista)


@bp.post("/usuarios/<int:uid>/alternar")
@roles_required("admin")
def alternar(uid):
    db = get_db()
    u = db.um("SELECT id, perfil, ativo, nome FROM usuarios WHERE id = %s", (uid,))
    if not u:
        abort(404)
    if u["perfil"] == "admin":
        flash("Administradores não podem ser desativados por aqui.", "erro")
    else:
        novo = 0 if u["ativo"] else 1
        db.executar("UPDATE usuarios SET ativo = %s WHERE id = %s", (novo, uid))
        flash(f"Conta de {u['nome']} {'ativada' if novo else 'desativada'}.", "sucesso")
    return redirect(url_for("admin.usuarios"))


@bp.get("/relatorios")
@roles_required("admin")
def relatorios():
    db = get_db()
    por_categoria = db.consultar(
        """SELECT c.nome AS rotulo, COUNT(p.usuario_id) AS total
           FROM categorias c LEFT JOIN prestadores p ON p.categoria_id = c.id
           GROUP BY c.id, c.nome ORDER BY total DESC, c.nome"""
    )
    por_cidade = db.consultar(
        """SELECT cidade AS rotulo, COUNT(*) AS total FROM prestadores
           GROUP BY cidade ORDER BY total DESC, cidade LIMIT 15"""
    )
    por_status = db.consultar("SELECT status AS rotulo, COUNT(*) AS total FROM servicos GROUP BY status")
    for r in por_status:
        r["rotulo"] = STATUS_SERVICO.get(r["rotulo"], r["rotulo"])
    meses = Counter(_mes(r["criado_em"]) for r in db.consultar("SELECT criado_em FROM servicos"))
    por_mes = [{"rotulo": m, "total": t} for m, t in sorted(meses.items())]
    media = db.um("SELECT AVG(avaliacao) AS m, COUNT(avaliacao) AS n FROM servicos WHERE avaliacao IS NOT NULL")
    return render_template(
        "admin/relatorios.html",
        blocos=[
            ("Prestadores por categoria", "prestadores_por_categoria", por_categoria),
            ("Prestadores por cidade", "prestadores_por_cidade", por_cidade),
            ("Serviços por status", "servicos_por_status", por_status),
            ("Serviços solicitados por mês", "servicos_por_mes", por_mes),
        ],
        media=round(float(media["m"]), 2) if media["m"] is not None else None,
        n_avaliacoes=media["n"],
    )


def _celula(v):
    s = "" if v is None else str(v)
    # evita injeção de fórmulas ao abrir o CSV no Excel/Sheets
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


EXPORTACOES = {
    "prestadores": (
        """SELECT u.id, u.nome, c.nome AS categoria, p.anos_experiencia, p.disponibilidade,
                  p.bairro, p.cidade, p.estado, p.latitude, p.longitude, p.visivel
           FROM prestadores p JOIN usuarios u ON u.id = p.usuario_id
           JOIN categorias c ON c.id = p.categoria_id ORDER BY u.id"""
    ),
    "servicos": (
        """SELECT s.id, c.nome AS categoria, s.status, s.data_prevista, s.criado_em,
                  s.concluido_em, s.avaliacao, s.prestador_id, s.contratante_id
           FROM servicos s JOIN categorias c ON c.id = s.categoria_id ORDER BY s.id"""
    ),
    "usuarios": "SELECT id, nome, email, perfil, ativo, criado_em FROM usuarios ORDER BY id",
}


@bp.get("/exportar/<tipo>.csv")
@roles_required("admin")
def exportar(tipo):
    sql = EXPORTACOES.get(tipo)
    if not sql:
        abort(404)
    linhas = get_db().consultar(sql)
    buf = io.StringIO()
    if linhas:
        w = csv.writer(buf, delimiter=";")
        w.writerow(linhas[0].keys())
        for r in linhas:
            w.writerow([_celula(v) for v in r.values()])
    return Response(
        "\ufeff" + buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=labu_{tipo}.csv"},
    )
