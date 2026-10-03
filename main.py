from flask import Flask, render_template, request, flash, redirect, session, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = '4532@BWJ23pslft'

@app.route('/')

def login():
    return render_template('login.html')

@app.route('/acesso' , methods=['POST'])
def acesso():
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    if email == 'admin' and senha == '456789':
        return render_template('home.html')
    else:
        flash('Email ou senha incorretos. Tente novamente.', 'danger')
        return redirect('/')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/cadastrando', methods=['POST'])
def cadastrando():
    nome = request.form.get('username')
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    # Modelo para o inicio da página
    tema = '#f1f1f1'
    img_capa = '/static/imagens/capa.png'
    img_perfil = '/static/imagens/foto_usuario.png'
    
    print(nome)
    print()
    print(senha)
    print()
    print(email)
    print()  
    print(tema)
    print()
    print(img_capa)
    print()
    print(img_perfil)
    
    return redirect('/cadastro')













if __name__ == '__main__':
    app.run(debug=True)