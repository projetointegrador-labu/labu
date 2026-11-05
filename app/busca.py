"""Busca de prestadores (texto, filtros, geolocalização e ordenação)."""
from flask import current_app

from .db import get_db
from .geo import caixa_delimitadora, haversine_km
from .seed import DISPONIBILIDADES
from .validators import coordenada, decimal_, numero

DIARIA_SEM_LIMITE = 500  # slider no máximo = "qualquer valor"

_NOTA = ("(SELECT AVG(s.avaliacao) FROM servicos s "
         "WHERE s.prestador_id = p.usuario_id AND s.avaliacao IS NOT NULL)")
_N_AVAL = ("(SELECT COUNT(s.avaliacao) FROM servicos s "
           "WHERE s.prestador_id = p.usuario_id AND s.avaliacao IS NOT NULL)")

CAMPOS = f"""
  u.id, u.nome, p.descricao, p.anos_experiencia, p.disponibilidade, p.valor_diaria,
  p.bairro, p.cidade, p.estado, p.latitude, p.longitude, p.raio_km,
  c.nome AS categoria, c.id AS categoria_id,
  {_NOTA} AS nota_media, {_N_AVAL} AS n_avaliacoes
"""


def buscar_prestadores(args, ids=None):
    """Retorna (lista, por_distancia). `ids` restringe a busca (usado em 'Salvos')."""
    db = get_db()
    if ids is not None and not ids:
        return [], False

    where = ["p.visivel = 1", "u.ativo = 1"]
    params = []

    if ids:
        where.append(f"u.id IN ({','.join(['%s'] * len(ids))})")
        params += list(ids)

    q = (args.get("q") or "").strip()
    if q:
        like = f"%{q}%"
        where.append(
            "(p.cidade LIKE %s OR p.bairro LIKE %s OR c.nome LIKE %s OR EXISTS ("
            "SELECT 1 FROM prestador_habilidades h "
            "WHERE h.usuario_id = p.usuario_id AND h.habilidade LIKE %s))"
        )
        params += [like] * 4

    categoria = numero(args.get("categoria"), 1, 10**9)
    if categoria:
        where.append("p.categoria_id = %s")
        params.append(categoria)
    for campo, coluna in (("bairro", "p.bairro"), ("cidade", "p.cidade")):
        valor = (args.get(campo) or "").strip()
        if valor:
            where.append(f"{coluna} LIKE %s")
            params.append(f"%{valor}%")
    estado = (args.get("estado") or "").strip().upper()
    if len(estado) == 2:
        where.append("p.estado = %s")
        params.append(estado)
    if args.get("disponibilidade") in DISPONIBILIDADES:
        where.append("p.disponibilidade = %s")
        params.append(args["disponibilidade"])

    diaria_max = numero(args.get("diaria_max"), 0, 100000)
    if diaria_max is not None and diaria_max < DIARIA_SEM_LIMITE:
        where.append("p.valor_diaria IS NOT NULL AND p.valor_diaria <= %s")
        params.append(diaria_max)

    nota_min = decimal_(args.get("nota_min"), 0, 5)
    if nota_min:
        where.append(f"{_NOTA} >= %s")
        params.append(nota_min)

    lat = coordenada(args.get("lat"), -90, 90)
    lng = coordenada(args.get("lng"), -180, 180)
    raio = numero(args.get("raio"), 1, 200)  # None = qualquer distância
    por_distancia = lat is not None and lng is not None

    if por_distancia and raio:
        lat_min, lat_max, lng_min, lng_max = caixa_delimitadora(lat, lng, raio)
        where.append("p.latitude BETWEEN %s AND %s AND p.longitude BETWEEN %s AND %s")
        params += [lat_min, lat_max, lng_min, lng_max]

    rows = db.consultar(
        f"""SELECT {CAMPOS}
            FROM prestadores p
            JOIN usuarios u ON u.id = p.usuario_id
            JOIN categorias c ON c.id = p.categoria_id
            WHERE {' AND '.join(where)}
            LIMIT 500""",
        params,
    )

    for r in rows:
        for k in ("latitude", "longitude", "valor_diaria"):
            r[k] = float(r[k]) if r[k] is not None else None
        r["nota_media"] = round(float(r["nota_media"]), 1) if r["nota_media"] is not None else None
        r["distancia_km"] = None

    if por_distancia:
        mantidos = []
        for r in rows:
            if r["latitude"] is None:
                if not raio:  # sem raio: mantém, mas sem distância
                    mantidos.append(r)
                continue
            d = haversine_km(lat, lng, r["latitude"], r["longitude"])
            if raio and d > raio:
                continue
            r["distancia_km"] = round(d, 1)
            mantidos.append(r)
        rows = mantidos

    ordem = args.get("ordem") if args.get("ordem") in ("perto", "nota", "preco") else "perto"
    if ordem == "nota":
        rows.sort(key=lambda r: (-(r["nota_media"] or 0), -(r["n_avaliacoes"] or 0), r["nome"]))
    elif ordem == "preco":
        rows.sort(key=lambda r: (r["valor_diaria"] is None, r["valor_diaria"] or 0, r["nome"]))
    elif por_distancia:
        rows.sort(key=lambda r: (r["distancia_km"] is None, r["distancia_km"] or 0, r["nome"]))
    else:
        rows.sort(key=lambda r: (r["cidade"] or "", r["nome"]))

    rows = rows[: current_app.config["MAX_RESULTADOS"]]

    for r in rows:
        r["habilidades"], r["fotos"] = [], []
    if rows:
        idl = [r["id"] for r in rows]
        marcas = ",".join(["%s"] * len(idl))
        por_id = {r["id"]: r for r in rows}
        for h in db.consultar(
            f"SELECT usuario_id, habilidade FROM prestador_habilidades "
            f"WHERE usuario_id IN ({marcas}) ORDER BY posicao, habilidade", idl):
            por_id[h["usuario_id"]]["habilidades"].append(h["habilidade"])
        for f in db.consultar(
            f"SELECT usuario_id, url FROM prestador_fotos WHERE usuario_id IN ({marcas}) ORDER BY id", idl):
            por_id[f["usuario_id"]]["fotos"].append(f["url"])

    return rows, por_distancia
