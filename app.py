from flask import Flask, render_template, request, redirect, session, send_file
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'


# ================= CONEXÃO POSTGRES =================
def conectar():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode='require'
    )

# ================= CRIAR BANCO =================
def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        senha TEXT,
        tipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registros (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        telefone TEXT,
        material TEXT,
        data_saida TEXT,
        hora_saida TEXT,
        data_devolucao TEXT,
        hora_devolucao TEXT,
        usuario TEXT
    )
    """)

    cursor.execute("SELECT * FROM usuarios WHERE username = %s", ('admin',))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (username, senha, tipo) VALUES (%s, %s, %s)",
            ('admin', generate_password_hash('admin123'), 'admin')
        )

    conn.commit()
    conn.close()

criar_banco()


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], senha):
            session['usuario'] = user[1]
            session['tipo'] = user[3]
            return redirect('/dashboard')
        else:
            return "Login inválido"

    return render_template('login.html')


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ================= DASHBOARD =================
@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM registros ORDER BY id DESC")
    dados = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html', dados=dados)


# ================= CADASTRAR =================
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    if 'usuario' not in session:
        return redirect('/login')

    nome = request.form['nome']
    telefone = request.form['telefone']
    material = request.form['material']

    agora = datetime.now()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO registros (nome, telefone, material, data_saida, hora_saida, usuario)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        nome,
        telefone,
        material,
        agora.strftime('%d/%m/%Y'),
        agora.strftime('%H:%M'),
        session['usuario']
    ))

    conn.commit()
    conn.close()

    return redirect('/dashboard')


# ================= DEVOLVER =================
@app.route('/devolver/<int:id>')
def devolver(id):
    conn = conectar()
    cursor = conn.cursor()

    agora = datetime.now()

    cursor.execute("""
    UPDATE registros
    SET data_devolucao = %s, hora_devolucao = %s
    WHERE id = %s
    """, (
        agora.strftime('%d/%m/%Y'),
        agora.strftime('%H:%M'),
        id
    ))

    conn.commit()
    conn.close()

    return redirect('/dashboard')


# ================= RELATÓRIO =================
@app.route('/relatorio')
def relatorio():
    conn = conectar()

    df = pd.read_sql_query("SELECT * FROM registros", conn)

    caminho = "relatorio.xlsx"
    df.to_excel(caminho, index=False)

    conn.close()

    return send_file(caminho, as_attachment=True)


# ================= ADMIN =================
@app.route('/admin')
def admin():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return "Acesso negado"

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios ORDER BY id")
    usuarios = cursor.fetchall()

    conn.close()

    return render_template('admin.html', usuarios=usuarios)


# ================= CRIAR USUÁRIO =================
@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    if session.get('tipo') != 'admin':
        return "Acesso negado"

    username = request.form['username']
    senha = generate_password_hash(request.form['senha'])
    tipo = request.form['tipo']

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO usuarios (username, senha, tipo)
    VALUES (%s, %s, %s)
    """, (username, senha, tipo))

    conn.commit()
    conn.close()

    return redirect('/admin')


# ================= EXCLUIR USUÁRIO =================
@app.route('/deletar_usuario/<int:id>')
def deletar_usuario(id):
    if session.get('tipo') != 'admin':
        return "Acesso negado"

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM usuarios WHERE id = %s", (id,))
    user = cursor.fetchone()

    if user and user[0] == 'admin':
        return "Não pode excluir o admin principal"

    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')


if __name__ == '__main__':
    app.run(debug=True)