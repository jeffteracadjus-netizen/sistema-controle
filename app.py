from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'


# ================= BANCO =================
def criar_banco():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        senha TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        telefone TEXT,
        material TEXT,
        data_saida TEXT,
        hora_saida TEXT,
        data_devolucao TEXT,
        hora_devolucao TEXT,
        usuario TEXT
    )
    ''')

    conn.commit()
    conn.close()


criar_banco()


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], senha):
            session['usuario'] = username
            return redirect('/')
        else:
            return "Login inválido"

    return render_template('login.html')


# ================= REGISTRO =================
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        username = request.form['username']
        senha = generate_password_hash(request.form['senha'])

        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (username, senha))
            conn.commit()
            return redirect('/login')
        except:
            return "Usuário já existe"

    return render_template('registrar.html')


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/login')


# ================= HOME =================
@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM registros")
    dados = cursor.fetchall()

    conn.close()

    return render_template('index.html', dados=dados)


# ================= CADASTRAR MATERIAL =================
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    if 'usuario' not in session:
        return redirect('/login')

    nome = request.form['nome']
    telefone = request.form['telefone']
    material = request.form['material']

    agora = datetime.now()

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO registros (nome, telefone, material, data_saida, hora_saida, usuario)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        nome,
        telefone,
        material,
        agora.strftime('%d/%m/%Y'),
        agora.strftime('%H:%M'),
        session['usuario']
    ))

    conn.commit()
    conn.close()

    return redirect('/')


# ================= DEVOLUÇÃO =================
@app.route('/devolver/<int:id>')
def devolver(id):
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    agora = datetime.now()

    cursor.execute('''
    UPDATE registros
    SET data_devolucao = ?, hora_devolucao = ?
    WHERE id = ?
    ''', (
        agora.strftime('%d/%m/%Y'),
        agora.strftime('%H:%M'),
        id
    ))

    conn.commit()
    conn.close()

    return redirect('/')


# ================= RELATÓRIO =================
@app.route('/relatorio')
def relatorio():
    conn = sqlite3.connect('banco.db')

    df = pd.read_sql_query("SELECT * FROM registros", conn)

    caminho = "relatorio.xlsx"
    df.to_excel(caminho, index=False)

    conn.close()

    return send_file(caminho, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)