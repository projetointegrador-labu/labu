from flask import Flask, render_template, request, flash, redirect, session, jsonify








app = Flask(__name__)
app.config['SECRET_KEY'] = '4532@BWJ23pslft'

@app.route('/')

def login():
    return render_template('login.html')

@app.route('/acesso' , methods=['POST'])
def acesso():
    nome = request.form.get['email']
    senha = request.form.get['senha']
    return render_template('/home.html')














if __name__ == '__main__':
    app.run(debug=True)