"""Geolocalização"""
import math

RAIO_TERRA_KM = 6371.0088


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


def caixa_delimitadora(lat, lng, raio_km):
    """Retângulo (lat_min, lat_max, lng_min, lng_max) que contém o círculo de busca."""
    dlat = math.degrees(raio_km / RAIO_TERRA_KM)
    cos_lat = max(math.cos(math.radians(lat)), 0.01)
    dlng = math.degrees(raio_km / (RAIO_TERRA_KM * cos_lat))
    return lat - dlat, lat + dlat, lng - dlng, lng + dlng
