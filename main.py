from flask import Flask, render_template, request, flash, redirect, session, jsonify, g
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = '4532@BWJ23pslft'
app.config['DATABASE'] = 'labu.db'

# Banco de dados SQLite
def get_db():
    if 'bd' not in g:
        g.bd = sqlite3.connect(app.config['DATABASE'],
        detect_types = sqlite3.PARSE_DECLTYPES)
        g.bd.row_factory = sqlite3.Row
    return g.bd

@app.teardown_appcontext
def close_db(error):
    db = g.pop('bd', None)
    if db is not None:
        db.close()

def create_table():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL,
            tema TEXT DEFAULT '#f1f1f1',
            img_capa TEXT DEFAULT '/static/imagens/capa.png',
            img_perfil TEXT DEFAULT '/static/imagens/foto_usuario.png'
        );
    ''')
    db.commit()

with app.app_context():
    create_table()
    
# Tela de login
@app.route('/')
def login():
    return render_template('login.html')

# Tela de acesso
@app.route('/acesso' , methods=['POST'])
def acesso():
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    if email == 'admin' and senha == '456789':
        return render_template('home.html')
    else:
        flash('Email ou senha incorretos. Tente novamente.', 'danger')
        return redirect('/')

# Tela para mostrar cadastro
@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

# Tela para cadastro
@app.route('/cadastrando', methods=['POST'])
def cadastrando():
    nome = request.form.get('username')
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    # Modelo para o inicio da página
    tema = '#f1f1f1'
    img_capa = '/static/imagens/capa.png'
    img_perfil = '/static/imagens/foto_usuario.png'
    
    return redirect('/cadastro')













if __name__ == '__main__':
    app.run(debug=True)