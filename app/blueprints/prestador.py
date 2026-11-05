from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..security import roles_required
from ..seed import DISPONIBILIDADES
from ..validators import (cep_valido, coordenada, decimal_, numero, so_digitos, telefone_valido,
                          uf_valida, url_imagem_valida)

bp = Blueprint("prestador", __name__, url_prefix="/prestador")


def _salvar_listas(db, uid, habilidades, fotos):
    db.executar("DELETE FROM prestador_habilidades WHERE usuario_id = %s", (uid,))
    for i, h in enumerate(habilidades):
        db.executar("INSERT INTO prestador_habilidades (usuario_id, habilidade, posicao) VALUES (%s, %s, %s)",
                    (uid, h, i))
    db.executar("DELETE FROM prestador_fotos WHERE usuario_id = %s", (uid,))
    for url in fotos:
        db.executar("INSERT INTO prestador_fotos (usuario_id, url) VALUES (%s, %s)", (uid, url))


def _separar_habilidades(texto):
    vistos, lista = set(), []
    for h in (texto or "").split(","):
        h = " ".join(h.split())
        if h and h.lower() not in vistos:
            vistos.add(h.lower())
            lista.append(h)
    return lista


@bp.route("/perfil", methods=["GET", "POST"])
@roles_required("prestador")
def perfil():
    db = get_db()
    categorias = db.consultar("SELECT id, nome FROM categorias ORDER BY nome")
    atual = db.um("SELECT * FROM prestadores WHERE usuario_id = %s", (g.user["id"],)) or {}
    erros, form = {}, dict(atual)
    if atual:
        form["habilidades"] = ", ".join(r["habilidade"] for r in db.consultar(
            "SELECT habilidade FROM prestador_habilidades WHERE usuario_id = %s ORDER BY posicao", (g.user["id"],)))
        for i, r in enumerate(db.consultar(
                "SELECT url FROM prestador_fotos WHERE usuario_id = %s ORDER BY id", (g.user["id"],)), start=1):
            form[f"foto{i}"] = r["url"]
        if form.get("valor_diaria") is not None:
            form["valor_diaria"] = int(float(form["valor_diaria"])) if float(form["valor_diaria"]).is_integer() else form["valor_diaria"]

    if request.method == "POST":
        f = request.form
        form = {k: (f.get(k) or "").strip() for k in
                ("categoria_id", "descricao", "anos_experiencia", "disponibilidade", "whatsapp",
                 "cep", "bairro", "cidade", "estado", "latitude", "longitude", "raio_km",
                 "valor_diaria", "habilidades", "foto1", "foto2", "foto3")}
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
        diaria = None
        if form["valor_diaria"]:
            diaria = decimal_(form["valor_diaria"], 0, 5000)
            if diaria is None:
                erros["valor_diaria"] = "Informe um valor entre 0 e 5000 (ou deixe em branco)."
        habilidades = _separar_habilidades(form["habilidades"])
        if len(habilidades) > 8:
            erros["habilidades"] = "Informe no máximo 8 habilidades."
        elif any(len(h) > 40 for h in habilidades):
            erros["habilidades"] = "Cada habilidade deve ter até 40 caracteres."
        fotos = []
        for n in (1, 2, 3):
            url = form[f"foto{n}"]
            if url:
                if url_imagem_valida(url):
                    fotos.append(url)
                else:
                    erros[f"foto{n}"] = "Use um endereço https:// de imagem, sem espaços."
        raio = numero(form["raio_km"], 1, 200)
        if raio is None:
            erros["raio_km"] = "Informe um valor entre 1 e 200 km."

        if not erros:
            valores = (categoria_id, form["descricao"] or None, anos, form["disponibilidade"],
                       so_digitos(form["whatsapp"]) or None, so_digitos(form["cep"]) or None,
                       form["bairro"] or None, form["cidade"], form["estado"], lat, lng, raio,
                       diaria, form["visivel"])
            if atual:
                db.executar(
                    """UPDATE prestadores SET categoria_id=%s, descricao=%s, anos_experiencia=%s,
                       disponibilidade=%s, whatsapp=%s, cep=%s, bairro=%s, cidade=%s, estado=%s,
                       latitude=%s, longitude=%s, raio_km=%s, valor_diaria=%s, visivel=%s, atualizado_em=CURRENT_TIMESTAMP
                       WHERE usuario_id=%s""",
                    valores + (g.user["id"],),
                )
            else:
                db.executar(
                    """INSERT INTO prestadores (categoria_id, descricao, anos_experiencia, disponibilidade,
                       whatsapp, cep, bairro, cidade, estado, latitude, longitude, raio_km, valor_diaria, visivel, usuario_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    valores + (g.user["id"],),
                )
            _salvar_listas(db, g.user["id"], habilidades, fotos)
            if lat is None:
                flash("Perfil salvo. Dica: informe sua localização no mapa para aparecer nas buscas por proximidade.", "aviso")
            else:
                flash("Perfil profissional salvo!", "sucesso")
            return redirect(url_for("prestador.perfil"))
    elif not atual:
        form = {"disponibilidade": "imediata", "raio_km": 10, "anos_experiencia": 0, "visivel": 1}

    return render_template("prestador_form.html", form=form, erros=erros, categorias=categorias,
                           ja_cadastrado=bool(atual))
