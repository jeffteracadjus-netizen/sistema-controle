from flask import Flask, render_template, request, redirect, session, send_file
import psycopg2
import os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = "segredo_super_seguro"

# 🔗 CONEXÃO
def conectar():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode='require'
    )

# 🧱 CRIAR TABELAS + AJUSTAR BANCO
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # Tabela usuarios (sem tipo inicialmente)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Adiciona coluna tipo se não existir
    cursor.execute("""
    ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tipo TEXT DEFAULT 'funcionario'
    """)

    # Tabela registros
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registros (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        telefone TEXT,
        material TEXT,
        saida TIMESTAMP,
        devolucao TIMESTAMP
    )
    """)

    # Cria admin se não existir
    cursor.execute("""
    INSERT INTO usuarios (username, password, tipo)
    VALUES ('admin', '1234', 'admin')
    ON CONFLICT (username) DO NOTHING
    """)

    # Garante que admin sempre seja admin
    cursor.execute("""
    UPDATE usuarios SET tipo='admin' WHERE username='admin'
    """)

    conn.commit()
    cursor.close()
    conn.close()

# 🚨 IMPORTANTE: CHAMA A FUNÇÃO
criar_tabelas()

# 🔐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, tipo FROM usuarios WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session["usuario"] = user[0]
            session["tipo"] = user[1]
            return redirect("/dashboard")
        else:
            return "Usuário ou senha inválidos"

    return render_template("login.html")

# 🚫 BLOQUEAR REGISTRO PÚBLICO
@app.route("/registrar")
def registrar():
    return redirect("/")

# 👑 ADMIN CRIA USUÁRIO
@app.route("/criar_usuario", methods=["POST"])
def criar_usuario():
    if session.get("tipo") != "admin":
        return "Acesso negado"

    username = request.form["username"]
    password = request.form["password"]

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO usuarios (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
    except:
        cursor.close()
        conn.close()
        return "Usuário já existe"

    cursor.close()
    conn.close()

    return redirect("/dashboard")

# 📊 DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "usuario" not in session:
        return redirect("/")

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        material = request.form["material"]

        cursor.execute(
            "INSERT INTO registros (nome, telefone, material, saida, devolucao) VALUES (%s, %s, %s, %s, %s)",
            (nome, telefone, material, datetime.now(), None)
        )
        conn.commit()

    cursor.execute("SELECT nome, telefone, material, saida, devolucao FROM registros")
    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("dashboard.html", dados=dados)

# 📥 RELATÓRIO
@app.route("/relatorio")
def relatorio():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT nome, telefone, material, saida, devolucao FROM registros")
    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    df = pd.DataFrame(dados, columns=["Nome", "Telefone", "Material", "Saída", "Devolução"])
    caminho = "relatorio.xlsx"
    df.to_excel(caminho, index=False)

    return send_file(caminho, as_attachment=True)

# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)