from app.geo import caixa_delimitadora, haversine_km


def test_haversine_sp_rio():
    d = haversine_km(-23.5505, -46.6333, -22.9068, -43.1729)
    assert 355 < d < 365


def test_distancia_zero():
    assert haversine_km(-23.5, -46.6, -23.5, -46.6) == 0


def test_caixa_contem_ponto_no_raio():
    lat, lng = -23.55, -46.63
    lat_min, lat_max, lng_min, lng_max = caixa_delimitadora(lat, lng, 10)
    assert lat_min < lat < lat_max and lng_min < lng < lng_max
    assert abs(haversine_km(lat, lng, lat_max, lng) - 10) < 0.1
