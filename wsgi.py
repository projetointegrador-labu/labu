"""Ponto de entrada WSGI (gunicorn wsgi:app) e CLI (flask --app wsgi ...)."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)