from flask import Blueprint, jsonify, request, url_for

from ..busca import buscar_prestadores

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/prestadores")
def prestadores():
    """Lista pública de prestadores (sem dados de contato) para o mapa."""
    resultados, _ = buscar_prestadores(request.args)
    return jsonify(
        [
            {
                "id": r["id"],
                "nome": r["nome"],
                "categoria": r["categoria"],
                "bairro": r["bairro"],
                "cidade": r["cidade"],
                "estado": r["estado"],
                "lat": r["latitude"],
                "lng": r["longitude"],
                "distancia_km": r["distancia_km"],
                "url": url_for("main.prestador", uid=r["id"]),
            }
            for r in resultados
            if r["latitude"] is not None and r["longitude"] is not None
        ]
    )
