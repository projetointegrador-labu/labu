import pytest

from app.db import get_db
from tests.conftest import cadastrar, entrar, perfil_prestador, sair, token


def test_paginas_publicas(client):
    for url in ("/", "/buscar", "/cadastro", "/entrar", "/privacidade", "/acessibilidade"):
        assert client.get(url).status_code == 200, url
    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.get("/nao-existe").status_code == 404


def test_acessibilidade_basica_no_html(client):
    html = client.get("/").get_data(as_text=True)
    assert 'lang="pt-BR"' in html
    assert 'class="skip-link"' in html
    assert 'aria-label="Navegação principal"' in html
    assert "acessibilidade.js" in html


def test_post_sem_csrf_e_rejeitado(client):
    r = client.post("/entrar", data={"email": "a@a.com", "senha": "x"})
    assert r.status_code == 400


def test_cadastro_validacoes(client):
    r = client.post("/cadastro", data={"csrf_token": token(client), "nome": "A", "email": "ruim",
                                       "perfil": "contratante", "senha": "123", "confirmar": "1"})
    html = r.get_data(as_text=True)
    assert "e-mail válido" in html and "pelo menos 8" in html and "LGPD" in html


def test_fluxo_completo(client, app):
    # prestador se cadastra e cria perfil
    r = cadastrar(client, "Carlos Almeida", "carlos@x.com", "prestador")
    assert "Perfil profissional" in r.get_data(as_text=True)
    r = perfil_prestador(client)
    assert "Perfil profissional salvo" in r.get_data(as_text=True)
    sair(client)

    # busca pública (sem contato visível)
    r = client.get("/buscar?cidade=São Paulo")
    assert "Carlos Almeida" in r.get_data(as_text=True)
    detalhe = client.get("/prestadores/1").get_data(as_text=True)
    assert "11988887777" not in detalhe and "(11) 98888-7777" not in detalhe

    # contratante solicita serviço
    cadastrar(client, "Maria Souza", "maria@x.com", "contratante")
    detalhe = client.get("/prestadores/1").get_data(as_text=True)
    assert "(11) 98888-7777" in detalhe
    r = client.post("/servicos/novo/1", data={"csrf_token": token(client, "/servicos/novo/1"),
                                              "descricao": "Reforma do banheiro completo"},
                    follow_redirects=True)
    assert "Solicitação enviada" in r.get_data(as_text=True)
    sair(client)

    # prestador aceita e conclui
    entrar(client, "carlos@x.com")
    t = token(client, "/servicos")
    client.post("/servicos/1/status", data={"csrf_token": t, "status": "aceito"})
    r = client.post("/servicos/1/status", data={"csrf_token": t, "status": "concluido"}, follow_redirects=True)
    assert "Concluído" in r.get_data(as_text=True)
    # transição inválida
    r = client.post("/servicos/1/status", data={"csrf_token": t, "status": "aceito"}, follow_redirects=True)
    assert "não é permitida" in r.get_data(as_text=True)
    sair(client)

    # contratante avalia
    entrar(client, "maria@x.com")
    t = token(client, "/servicos")
    r = client.post("/servicos/1/avaliar", data={"csrf_token": t, "nota": "5", "comentario": "Ótimo!"},
                    follow_redirects=True)
    assert "Obrigado" in r.get_data(as_text=True)
    assert "5 de 5" in client.get("/prestadores/1").get_data(as_text=True)


def test_busca_por_proximidade(client):
    cadastrar(client, "Perto Silva", "perto@x.com", "prestador")
    perfil_prestador(client, lat="-23.7627", lng="-46.6973")
    sair(client)
    cadastrar(client, "Longe Lima", "longe@x.com", "prestador")
    perfil_prestador(client, lat="-22.9068", lng="-43.1729", cidade="Rio de Janeiro")
    sair(client)

    dados = client.get("/api/prestadores?lat=-23.76&lng=-46.69&raio=15").get_json()
    assert [d["nome"] for d in dados] == ["Perto Silva"]
    assert dados[0]["distancia_km"] < 2
    assert "telefone" not in dados[0] and "whatsapp" not in dados[0]
    todos = client.get("/api/prestadores").get_json()
    assert len(todos) == 2


def test_permissoes(client):
    cadastrar(client, "Maria Souza", "maria@x.com", "contratante")
    assert client.get("/prestador/perfil").status_code == 403
    assert client.get("/admin").status_code == 403
    sair(client)
    r = client.get("/admin")
    assert r.status_code == 302 and "/entrar" in r.headers["Location"]


def test_login_bloqueia_apos_falhas(client):
    cadastrar(client, "Maria Souza", "maria@x.com", "contratante")
    sair(client)
    for _ in range(5):
        entrar(client, "maria@x.com", "errada123")
    r = entrar(client, "maria@x.com", "Senha1234")
    assert "Muitas tentativas" in r.get_data(as_text=True)


def test_open_redirect_bloqueado(client):
    cadastrar(client, "Maria Souza", "maria@x.com", "contratante")
    sair(client)
    r = client.post("/entrar?next=//evil.com", data={"csrf_token": token(client, "/entrar"),
                    "email": "maria@x.com", "senha": "Senha1234"})
    assert r.headers["Location"] == "/"


def test_admin_relatorios_e_csv(client, app):
    from werkzeug.security import generate_password_hash
    with app.app_context():
        get_db().executar("INSERT INTO usuarios (nome,email,senha_hash,perfil) VALUES (%s,%s,%s,'admin')",
                          ("Admin", "admin@x.com", generate_password_hash("Admin12345")))
    cadastrar(client, "Carlos", "carlos@x.com", "prestador")
    perfil_prestador(client)
    sair(client)
    r = entrar(client, "admin@x.com", "Admin12345")
    assert "Painel do administrador" in r.get_data(as_text=True)
    assert client.get("/admin/relatorios").status_code == 200
    csv = client.get("/admin/exportar/prestadores.csv")
    assert csv.status_code == 200 and "Carlos" in csv.get_data(as_text=True)
    assert client.get("/admin/exportar/inexistente.csv").status_code == 404
    assert client.get("/admin/usuarios").status_code == 200


def test_excluir_conta_lgpd(client, app):
    cadastrar(client, "Maria Souza", "maria@x.com", "contratante")
    t = token(client, "/conta")
    r = client.post("/conta/excluir", data={"csrf_token": t, "senha": "Senha1234"}, follow_redirects=True)
    assert "excluídos" in r.get_data(as_text=True)
    with app.app_context():
        assert get_db().um("SELECT id FROM usuarios WHERE email=%s", ("maria@x.com",)) is None
