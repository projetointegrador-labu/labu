import re

import pytest

from app import create_app, security
from app.db import get_db, init_schema


@pytest.fixture()
def app(tmp_path):
    security._TENTATIVAS.clear()  # isola o limitador de login entre testes
    app = create_app({"TESTING": True, "DB_BACKEND": "sqlite", "MYSQL": None,
                      "SQLITE_PATH": str(tmp_path / "t.db"), "SECRET_KEY": "teste",
                      "SESSION_COOKIE_SECURE": False})
    with app.app_context():
        init_schema(get_db())
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def token(client, url="/cadastro"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def cadastrar(client, nome, email, perfil, senha="Senha1234"):
    return client.post("/cadastro", data={
        "csrf_token": token(client), "nome": nome, "email": email, "perfil": perfil,
        "senha": senha, "confirmar": senha, "consentimento": "1"}, follow_redirects=True)


def sair(client):
    t = token(client, "/")
    client.post("/sair", data={"csrf_token": t})


def entrar(client, email, senha="Senha1234"):
    return client.post("/entrar", data={"csrf_token": token(client, "/entrar"),
                                        "email": email, "senha": senha}, follow_redirects=True)


def perfil_prestador(client, lat="-23.7627", lng="-46.6973", categoria=1, cidade="São Paulo", **extra):
    dados = {
        "csrf_token": token(client, "/prestador/perfil"), "categoria_id": categoria,
        "descricao": "Experiência com reformas", "anos_experiencia": 5, "disponibilidade": "imediata",
        "whatsapp": "11988887777", "cep": "04800000", "bairro": "Grajaú", "cidade": cidade,
        "estado": "SP", "latitude": lat, "longitude": lng, "raio_km": 10, "visivel": "1"}
    dados.update(extra)
    return client.post("/prestador/perfil", data=dados, follow_redirects=True)
