from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..security import roles_required
from ..seed import DISPONIBILIDADES
from ..validators import coordenada, cep_valido, numero, so_digitos, telefone_valido, uf_valida

bp = Blueprint("prestador", __name__, url_prefix="/prestador")


@bp.route("/perfil", methods=["GET", "POST"])
@roles_required("prestador")
def perfil():
    db = get_db()
    categorias = db.consultar("SELECT id, nome FROM categorias ORDER BY nome")
    atual = db.um("SELECT * FROM prestadores WHERE usuario_id = %s", (g.user["id"],)) or {}
    erros, form = {}, dict(atual)

    if request.method == "POST":
        f = request.form
        form = {k: (f.get(k) or "").strip() for k in
                ("categoria_id", "descricao", "anos_experiencia", "disponibilidade", "whatsapp",
                 "cep", "bairro", "cidade", "estado", "latitude", "longitude", "raio_km")}
        form["visivel"] = 1 if f.get("visivel") else 0

        categoria_id = numero(form["categoria_id"], 1, 10**9)
        if not categoria_id or not any(c["id"] == categoria_id for c in categorias):
            erros["categoria_id"] = "Escolha sua especialidade."
        if len(form["descricao"]) > 1000:
            erros["descricao"] = "Use no máximo 1000 caracteres."
        anos = numero(form["anos_experiencia"], 0, 70)
        if anos is None:
            erros["anos_experiencia"] = "Informe um número entre 0 e 70."
        if form["disponibilidade"] not in DISPONIBILIDADES:
            erros["disponibilidade"] = "Escolha uma opção."
        if form["whatsapp"] and not telefone_valido(form["whatsapp"]):
            erros["whatsapp"] = "Número inválido. Use DDD + número."
        if form["cep"] and not cep_valido(form["cep"]):
            erros["cep"] = "CEP inválido (8 dígitos)."
        if len(form["cidade"]) < 2:
            erros["cidade"] = "Informe a cidade."
        form["estado"] = form["estado"].upper()
        if not uf_valida(form["estado"]):
            erros["estado"] = "Escolha o estado."
        lat = coordenada(form["latitude"], -90, 90) if form["latitude"] else None
        lng = coordenada(form["longitude"], -180, 180) if form["longitude"] else None
        if (form["latitude"] or form["longitude"]) and (lat is None or lng is None):
            erros["latitude"] = "Coordenadas inválidas."
        raio = numero(form["raio_km"], 1, 200)
        if raio is None:
            erros["raio_km"] = "Informe um valor entre 1 e 200 km."

        if not erros:
            valores = (categoria_id, form["descricao"] or None, anos, form["disponibilidade"],
                       so_digitos(form["whatsapp"]) or None, so_digitos(form["cep"]) or None,
                       form["bairro"] or None, form["cidade"], form["estado"], lat, lng, raio, form["visivel"])
            if atual:
                db.executar(
                    """UPDATE prestadores SET categoria_id=%s, descricao=%s, anos_experiencia=%s,
                       disponibilidade=%s, whatsapp=%s, cep=%s, bairro=%s, cidade=%s, estado=%s,
                       latitude=%s, longitude=%s, raio_km=%s, visivel=%s, atualizado_em=CURRENT_TIMESTAMP
                       WHERE usuario_id=%s""",
                    valores + (g.user["id"],),
                )
            else:
                db.executar(
                    """INSERT INTO prestadores (categoria_id, descricao, anos_experiencia, disponibilidade,
                       whatsapp, cep, bairro, cidade, estado, latitude, longitude, raio_km, visivel, usuario_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    valores + (g.user["id"],),
                )
            if lat is None:
                flash("Perfil salvo. Dica: informe sua localização no mapa para aparecer nas buscas por proximidade.", "aviso")
            else:
                flash("Perfil profissional salvo!", "sucesso")
            return redirect(url_for("prestador.perfil"))
    elif not atual:
        form = {"disponibilidade": "imediata", "raio_km": 10, "anos_experiencia": 0, "visivel": 1}

    return render_template("prestador_form.html", form=form, erros=erros, categorias=categorias,
                           ja_cadastrado=bool(atual))
