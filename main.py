from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '4532@BWJ23pslft'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///labu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Banco de dados SQLite

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tema = db.Column(db.String(20), default='#f1f1f1')
    img_capa = db.Column(db.String(255), default='/static/imagens/capa.png')
    img_perfil = db.Column(db.String(255), default='/static/imagens/foto_usuario.png')

with app.app_context():
    db.create_all()

# Tela de login
@app.route('/')
def login():
    return render_template('login.html')

# Tela de acesso
@app.route('/acesso' , methods=['POST'])
def acesso():
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    usuario = Usuario.query.filter_by(email=email, senha=senha).first()
    
    if usuario:
        session['nome'] = usuario.nome
        session['email'] = usuario.email
        return redirect('/home')
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
    
    novo_usuario = Usuario(nome=nome, email=email, senha=senha)
    
    db.session.add(novo_usuario)
    db.session.commit()
    
    session['nome'] = nome
    session['email'] = email

    flash(f'Cadastro realizado com sucesso! Seja bem-vindo, {nome}!', 'success')
    return redirect('/home')

@app.route('/home')
def home():
    email = session.get('email')
    nome = session.get('nome')
    
    if not email:
        return redirect('/')
    return render_template('home.html', email=email, nome=nome)

@app.route('/logout')
def logout():    
    session.clear()
    return redirect('/')









if __name__ == '__main__':
    app.run(debug=True)