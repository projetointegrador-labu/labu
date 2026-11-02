from flask import Blueprint, abort, g, jsonify, render_template, request

from ..busca import buscar_prestadores
from ..db import get_db

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    db = get_db()
    categorias = db.consultar("SELECT id, nome FROM categorias ORDER BY nome")
    total = db.um("SELECT COUNT(*) AS n FROM prestadores WHERE visivel = 1")["n"]
    return render_template("index.html", categorias=categorias, total_prestadores=total)


@bp.get("/buscar")
def buscar():
    db = get_db()
    categorias = db.consultar("SELECT id, nome FROM categorias ORDER BY nome")
    resultados, por_distancia = buscar_prestadores(request.args)
    return render_template(
        "busca.html",
        categorias=categorias,
        resultados=resultados,
        por_distancia=por_distancia,
        filtros=request.args,
    )


@bp.get("/prestadores/<int:uid>")
def prestador(uid):
    db = get_db()
    p = db.um(
        """SELECT u.id, u.nome, u.telefone, p.*, c.nome AS categoria
           FROM prestadores p JOIN usuarios u ON u.id = p.usuario_id
           JOIN categorias c ON c.id = p.categoria_id
           WHERE u.id = %s AND p.visivel = 1 AND u.ativo = 1""",
        (uid,),
    )
    if not p:
        abort(404)
    avaliacoes = db.consultar(
        """SELECT s.avaliacao, s.comentario, s.concluido_em, u.nome AS contratante
           FROM servicos s JOIN usuarios u ON u.id = s.contratante_id
           WHERE s.prestador_id = %s AND s.avaliacao IS NOT NULL
           ORDER BY s.concluido_em DESC LIMIT 20""",
        (uid,),
    )
    media = round(sum(a["avaliacao"] for a in avaliacoes) / len(avaliacoes), 1) if avaliacoes else None
    concluidos = db.um(
        "SELECT COUNT(*) AS n FROM servicos WHERE prestador_id = %s AND status = 'concluido'", (uid,)
    )["n"]
    return render_template("prestador_detalhe.html", p=p, avaliacoes=avaliacoes, media=media, concluidos=concluidos)


@bp.get("/privacidade")
def privacidade():
    return render_template("privacidade.html")


@bp.get("/acessibilidade")
def acessibilidade():
    return render_template("acessibilidade.html")


@bp.get("/health")
def health():
    """Usado pelo healthcheck do Railway."""
    try:
        get_db().um("SELECT 1 AS ok")
        return jsonify(status="ok"), 200
    except Exception:  # noqa: BLE001
        return jsonify(status="erro-banco"), 503
