"""Configuração da aplicação (variáveis de ambiente, compatível com Railway)."""
import os
from urllib.parse import urlparse, unquote


def _is_production() -> bool:
    return os.environ.get("APP_ENV", "").lower() == "production" or bool(
        os.environ.get("RAILWAY_ENVIRONMENT")
    )


def _mysql_settings():
    """Lê a conexão MySQL de MYSQL_URL / DATABASE_URL Railway."""
    for name in ("MYSQL_URL", "DATABASE_URL", "MYSQL_PUBLIC_URL"):
        url = os.environ.get(name, "")
        if url.startswith("mysql"):
            u = urlparse(url)
            return {
                "host": u.hostname,
                "port": u.port or 3306,
                "user": unquote(u.username or ""),
                "password": unquote(u.password or ""),
                "database": (u.path or "/").lstrip("/"),
            }
    if os.environ.get("MYSQLHOST"):
        return {
            "host": os.environ["MYSQLHOST"],
            "port": int(os.environ.get("MYSQLPORT", 3306)),
            "user": os.environ.get("MYSQLUSER", "root"),
            "password": os.environ.get("MYSQLPASSWORD", ""),
            "database": os.environ.get("MYSQLDATABASE", "railway"),
        }
    return None


class Config:
    IS_PRODUCTION = _is_production()

    SECRET_KEY = os.environ.get("SECRET_KEY") or (
        None if IS_PRODUCTION else "dev-only-change-me"
    )

    MYSQL = _mysql_settings()
    DB_BACKEND = "mysql" if MYSQL else "sqlite"
    SQLITE_PATH = os.environ.get("SQLITE_PATH", "labu_dev.db")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 horas

    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    VLIBRAS_ENABLED = os.environ.get("VLIBRAS_ENABLED", "true").lower() == "true"

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
    ADMIN_NOME = os.environ.get("ADMIN_NOME", "Administrador LABU")

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB
    MAX_RESULTADOS = 50

    @classmethod
    def validate(cls):
        if cls.IS_PRODUCTION:
            if not cls.SECRET_KEY:
                raise RuntimeError("Defina SECRET_KEY nas variáveis de ambiente.")
            if cls.DB_BACKEND != "mysql":
                raise RuntimeError(
                    "Produção exige MySQL. Defina MYSQL_URL (ou MYSQLHOST/MYSQLUSER/...)."
                )
