"""Fábrica da aplicação LABU."""
from datetime import date, datetime

import click
from dotenv import load_dotenv
from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash

load_dotenv()

from .config import Config  # noqa: E402
from .db import close_db, get_db, init_schema  # noqa: E402
from .security import carregar_usuario, csrf_token, verificar_csrf  # noqa: E402
from .seed import DISPONIBILIDADES, ESTADOS, STATUS_SERVICO  # noqa: E402


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    else:
        Config.validate()

    # Railway termina o TLS no proxy: respeitar X-Forwarded-*
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.teardown_appcontext(close_db)
    app.before_request(carregar_usuario)
    app.before_request(verificar_csrf)

    from .blueprints import admin, api, auth, main, prestador, servicos

    for bp in (main.bp, auth.bp, prestador.bp, servicos.bp, admin.bp, api.bp):
        app.register_blueprint(bp)

    @app.context_processor
    def contexto():
        return {
            "csrf_token": csrf_token,
            "maps_key": app.config["GOOGLE_MAPS_API_KEY"],
            "vlibras": app.config["VLIBRAS_ENABLED"],
            "ESTADOS": ESTADOS,
            "DISPONIBILIDADES": DISPONIBILIDADES,
            "STATUS_SERVICO": STATUS_SERVICO,
        }

    @app.template_filter("data_br")
    def data_br(valor, com_hora=False):
        if not valor:
            return "—"
        if isinstance(valor, str):
            try:
                valor = datetime.fromisoformat(valor)
            except ValueError:
                return valor
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M" if com_hora else "%d/%m/%Y")
        if isinstance(valor, date):
            return valor.strftime("%d/%m/%Y")
        return str(valor)

    @app.template_filter("zip")
    def zip_filter(a, b):
        return zip(a, b)

    @app.template_filter("telefone")
    def telefone(valor):
        d = "".join(c for c in (valor or "") if c.isdigit())
        if len(d) == 11:
            return f"({d[:2]}) {d[2:7]}-{d[7:]}"
        if len(d) == 10:
            return f"({d[:2]}) {d[2:6]}-{d[6:]}"
        return valor or ""

    @app.after_request
    def cabecalhos(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(self), camera=(), microphone=()")
        if request.endpoint not in ("static", None) and request.method == "GET":
            resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    for codigo, titulo, msg in (
        (400, "Requisição inválida", None),
        (403, "Acesso negado", "Você não tem permissão para acessar esta página."),
        (404, "Página não encontrada", "O endereço acessado não existe."),
        (500, "Erro interno", "Algo deu errado. Tente novamente em instantes."),
    ):
        def _handler(e, codigo=codigo, titulo=titulo, msg=msg):
            descricao = msg or getattr(e, "description", "")
            return render_template("erro.html", codigo=codigo, titulo=titulo, mensagem=descricao), codigo

        app.register_error_handler(codigo, _handler)

    registrar_cli(app)
    return app


def _criar_superusuario(db, nome, email, senha):
    existe = db.um("SELECT id FROM usuarios WHERE email = %s", (email.lower(),))
    if existe:
        return False
    db.executar(
        """INSERT INTO usuarios (nome, email, senha_hash, perfil, consentimento_lgpd, consentimento_em)
           VALUES (%s, %s, %s, 'admin', 1, CURRENT_TIMESTAMP)""",
        (nome, email.lower(), generate_password_hash(senha)),
    )
    return True


def registrar_cli(app):
    @app.cli.command("init-db")
    def init_db_cmd():
        """Cria as tabelas, as categorias e (se configurado) o superusuário."""
        with app.app_context():
            db = get_db()
            init_schema(db)
            click.echo("Banco de dados inicializado.")
            cfg = app.config
            if cfg["ADMIN_EMAIL"] and cfg["ADMIN_PASSWORD"]:
                if _criar_superusuario(db, cfg["ADMIN_NOME"], cfg["ADMIN_EMAIL"], cfg["ADMIN_PASSWORD"]):
                    click.echo(f"Superusuário criado: {cfg['ADMIN_EMAIL']}")
                else:
                    click.echo("Superusuário já existe.")

    @app.cli.command("create-superuser")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--senha", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_superuser_cmd(nome, email, senha):
        """Cria um superusuário (administrador)."""
        with app.app_context():
            ok = _criar_superusuario(get_db(), nome, email, senha)
            click.echo("Superusuário criado." if ok else "E-mail já cadastrado.")

    @app.cli.command("seed-demo")
    def seed_demo_cmd():
        """Insere prestadores fictícios (somente para demonstração/testes)."""
        from .demo import popular_demo

        with app.app_context():
            n = popular_demo(get_db())
            click.echo(f"{n} prestadores de demonstração criados (senha: Demo12345).")
