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


# ---------------- novo layout: filtros, favoritos, perfil estendido ----------------
def _criar_prestador(client, nome, email, **extra):
    cadastrar(client, nome, email, "prestador")
    r = perfil_prestador(client, **extra)
    sair(client)
    return r


def test_filtros_texto_diaria_e_habilidade(client):
    _criar_prestador(client, "Edson Lima", "edson@x.com", valor_diaria="180",
                     habilidades="Tomadas, Iluminação, Quadro de distribuição")
    ids = lambda qs: client.get("/api/prestadores" + qs).get_json()  # noqa: E731
    assert len(ids("?q=Tomadas")) == 1           # habilidade
    assert len(ids("?q=Pedreiro")) == 1          # função (categoria 1)
    assert len(ids("?q=inexistente")) == 0
    assert len(ids("?diaria_max=100")) == 0      # acima do limite
    assert len(ids("?diaria_max=200")) == 1
    assert len(ids("?diaria_max=500")) == 1      # 500 = sem limite
    html = client.get("/buscar?q=Tomadas").get_data(as_text=True)
    assert "Filtros" in html and "Chamar pelo site" in html and "R$ 180" in html and "Iluminação" in html


def test_nota_minima_e_ordenacao(client, app):
    _criar_prestador(client, "Bom Preco", "a@x.com", valor_diaria="100")
    _criar_prestador(client, "Boa Nota", "b@x.com", valor_diaria="300")
    with app.app_context():
        db = get_db()
        db.executar("INSERT INTO usuarios (nome,email,senha_hash) VALUES ('C','c@x.com','x')")
        cid = db.um("SELECT id FROM usuarios WHERE email='c@x.com'")["id"]
        for prest, nota in ((1, 3), (2, 5), (2, 5)):
            db.executar("""INSERT INTO servicos (prestador_id, contratante_id, categoria_id, descricao, status, avaliacao)
                           VALUES (%s,%s,1,'serviço de teste','concluido',%s)""", (prest, cid, nota))
    nomes = lambda qs: [d["nome"] for d in client.get("/api/prestadores" + qs).get_json()]  # noqa: E731
    assert nomes("?nota_min=4") == ["Boa Nota"]
    assert nomes("?nota_min=3") and len(nomes("?nota_min=3")) == 2
    assert nomes("?ordem=nota")[0] == "Boa Nota"
    assert nomes("?ordem=preco")[0] == "Bom Preco"
    assert "2 serviços avaliados" in client.get("/buscar?ordem=nota").get_data(as_text=True)


def test_distancia_qualquer_e_com_raio(client):
    _criar_prestador(client, "Perto", "p@x.com", lat="-23.7627", lng="-46.6973")
    _criar_prestador(client, "Longe", "l@x.com", lat="-22.9068", lng="-43.1729", cidade="Rio de Janeiro")
    base = "?lat=-23.76&lng=-46.69"
    assert [d["nome"] for d in client.get("/api/prestadores" + base).get_json()] == ["Perto", "Longe"]
    assert [d["nome"] for d in client.get("/api/prestadores" + base + "&raio=15").get_json()] == ["Perto"]


def test_favoritos(client):
    _criar_prestador(client, "Edson Lima", "edson@x.com")
    # anônimo
    r = client.get("/favoritos")
    assert r.status_code == 302 and "/entrar" in r.headers["Location"]
    cadastrar(client, "Maria Souza", "maria@x.com", "contratante")
    t = token(client, "/buscar")
    r = client.post("/favoritos/1/alternar", data={"csrf_token": t, "next": "/buscar?#prestador-1"}, follow_redirects=True)
    assert "Profissional salvo" in r.get_data(as_text=True)
    assert "Edson Lima" in client.get("/favoritos").get_data(as_text=True)
    assert "Salvo ✓" in client.get("/buscar").get_data(as_text=True)
    r = client.post("/favoritos/1/alternar", data={"csrf_token": t}, follow_redirects=True)
    assert "removido" in r.get_data(as_text=True)
    assert "Edson Lima" not in client.get("/favoritos").get_data(as_text=True)
    assert client.post("/favoritos/999/alternar", data={"csrf_token": t}).status_code == 404
    sair(client)
    # prestador não pode salvar
    entrar(client, "edson@x.com")
    assert client.get("/favoritos").status_code == 403


def test_perfil_valida_fotos_e_habilidades(client):
    cadastrar(client, "Edson Lima", "edson@x.com", "prestador")
    r = perfil_prestador(client, foto1="javascript:alert(1)")
    assert "endereço https://" in r.get_data(as_text=True)
    r = perfil_prestador(client, habilidades=",".join(f"h{i}" for i in range(9)))
    assert "no máximo 8" in r.get_data(as_text=True)
    r = perfil_prestador(client, valor_diaria="abc")
    assert "entre 0 e 5000" in r.get_data(as_text=True)
    r = perfil_prestador(client, valor_diaria="180", habilidades="A, B, a", foto1="https://exemplo.com/f.jpg")
    assert "Perfil profissional salvo" in r.get_data(as_text=True)
    form = client.get("/prestador/perfil").get_data(as_text=True)
    assert 'value="A, B"' in form and "https://exemplo.com/f.jpg" in form and 'value="180"' in form
    detalhe = client.get("/prestadores/1").get_data(as_text=True)
    assert "Trabalhos realizados" in detalhe and "R$ 180 por dia" in detalhe


def test_layout_novo_elementos_principais(client):
    html = client.get("/").get_data(as_text=True)
    for trecho in ("Como funciona", "Abrir o feed", "Cadastrar-se", "Tema claro", "Alto contraste"):
        assert trecho in html, trecho
    busca = client.get("/buscar").get_data(as_text=True)
    for trecho in ("Profissionais perto de você", "Usar minha localização", "Distância máxima",
                   "Avaliação mínima", "Limpar filtros", "Mais perto"):
        assert trecho in busca, trecho
