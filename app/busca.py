"""Busca de prestadores (texto + geolocalização)."""
from flask import current_app

from .db import get_db
from .geo import caixa_delimitadora, haversine_km
from .validators import coordenada, numero

CAMPOS = """
  u.id, u.nome, p.descricao, p.anos_experiencia, p.disponibilidade,
  p.bairro, p.cidade, p.estado, p.latitude, p.longitude, p.raio_km,
  c.nome AS categoria, c.id AS categoria_id
"""


def buscar_prestadores(args):
    db = get_db()
    where = ["p.visivel = 1", "u.ativo = 1"]
    params = []

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
    if args.get("disponibilidade") == "imediata":
        where.append("p.disponibilidade = %s")
        params.append("imediata")

    lat = coordenada(args.get("lat"), -90, 90)
    lng = coordenada(args.get("lng"), -180, 180)
    raio = numero(args.get("raio"), 1, 200, 15)
    por_distancia = lat is not None and lng is not None

    if por_distancia:
        lat_min, lat_max, lng_min, lng_max = caixa_delimitadora(lat, lng, raio)
        where.append("p.latitude BETWEEN %s AND %s AND p.longitude BETWEEN %s AND %s")
        params += [lat_min, lat_max, lng_min, lng_max]

    sql = f"""
      SELECT {CAMPOS}
      FROM prestadores p
      JOIN usuarios u ON u.id = p.usuario_id
      JOIN categorias c ON c.id = p.categoria_id
      WHERE {' AND '.join(where)}
      LIMIT 500
    """
    rows = db.consultar(sql, params)

    for r in rows:
        r["latitude"] = float(r["latitude"]) if r["latitude"] is not None else None
        r["longitude"] = float(r["longitude"]) if r["longitude"] is not None else None
        r["distancia_km"] = None

    if por_distancia:
        resultado = []
        for r in rows:
            d = haversine_km(lat, lng, r["latitude"], r["longitude"])
            if d <= raio:
                r["distancia_km"] = round(d, 1)
                resultado.append(r)
        resultado.sort(key=lambda r: r["distancia_km"])
        rows = resultado
    else:
        rows.sort(key=lambda r: (r["cidade"] or "", r["nome"]))

    return rows[: current_app.config["MAX_RESULTADOS"]], por_distancia
