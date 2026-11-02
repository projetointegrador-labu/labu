import re
import sqlite3
from pathlib import Path

from flask import current_app, g

from .seed import CATEGORIAS

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"


class Conexao:
    def __init__(self, raw, backend):
        self.raw = raw
        self.backend = backend

    def _sql(self, sql):
        return sql.replace("%s", "?") if self.backend == "sqlite" else sql

    def consultar(self, sql, params=()):
        cur = self.raw.cursor()
        cur.execute(self._sql(sql), tuple(params))
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def um(self, sql, params=()):
        rows = self.consultar(sql, params)
        return rows[0] if rows else None

    def executar(self, sql, params=()):
        cur = self.raw.cursor()
        cur.execute(self._sql(sql), tuple(params))
        last = cur.lastrowid
        cur.close()
        self.raw.commit()
        return last

    def fechar(self):
        try:
            self.raw.close()
        except Exception:  # noqa: BLE001
            pass


def _abrir(app_config):
    if app_config["DB_BACKEND"] == "mysql":
        import pymysql
        from pymysql.cursors import DictCursor

        cfg = app_config["MYSQL"]
        raw = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=10,
        )
        return Conexao(raw, "mysql")
    raw = sqlite3.connect(app_config["SQLITE_PATH"])
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    return Conexao(raw, "sqlite")


def get_db() -> Conexao:
    if "db" not in g:
        g.db = _abrir(current_app.config)
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.fechar()


def _sql_para_sqlite(sql: str) -> str:
    sql = re.sub(r",\s*INDEX\s+\w+\s*\([^)]*\)", "", sql)
    sql = sql.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    sql = re.sub(r"\)\s*ENGINE=[^;]*", ")", sql)
    return sql


def init_schema(db: Conexao):
    """Cria tabelas (se não existirem) e popula as categorias iniciais."""
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    script = re.sub(r"--[^\n]*", "", script)
    if db.backend == "sqlite":
        script = _sql_para_sqlite(script)
    for stmt in (s.strip() for s in script.split(";")):
        if stmt:
            cur = db.raw.cursor()
            cur.execute(stmt)
            cur.close()
    db.raw.commit()

    existentes = {r["nome"] for r in db.consultar("SELECT nome FROM categorias")}
    for nome in CATEGORIAS:
        if nome not in existentes:
            db.executar("INSERT INTO categorias (nome) VALUES (%s)", (nome,))
