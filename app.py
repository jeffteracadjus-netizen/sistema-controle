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

# 🧱 CRIAR / ATUALIZAR BANCO
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tipo TEXT DEFAULT 'funcionario'
    """)

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

    # ADMIN
    cursor.execute("""
    INSERT INTO usuarios (username, password, tipo)
    VALUES ('admin', '1234', 'admin')
    ON CONFLICT (username) DO NOTHING
    """)

    cursor.execute("""
    UPDATE usuarios SET tipo='admin' WHERE username='admin'
    """)

    conn.commit()
    cursor.close()
    conn.close()

# 🔥 CHAMA AO INICIAR
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
            "SELECT id, username, tipo FROM usuarios WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session["usuario"] = user[1]
            session["tipo"] = user[2]
            return redirect("/dashboard")
        else:
            return "Usuário ou senha inválidos"

    return render_template("login.html")

# 🚫 BLOQUEAR REGISTRO PÚBLICO
@app.route("/registrar")
def registrar():
    return redirect("/")

# 👑 CRIAR USUÁRIO
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

# ❌ EXCLUIR USUÁRIO
@app.route("/excluir_usuario/<int:id>")
def excluir_usuario(id):
    if session.get("tipo") != "admin":
        return "Acesso negado"

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id = %s AND username != 'admin'", (id,))
    conn.commit()

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

    # REGISTRO DE MATERIAL
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        material = request.form["material"]

        cursor.execute(
            "INSERT INTO registros (nome, telefone, material, saida, devolucao) VALUES (%s, %s, %s, %s, %s)",
            (nome, telefone, material, datetime.now(), None)
        )
        conn.commit()

    # DADOS
    cursor.execute("SELECT nome, telefone, material, saida, devolucao FROM registros")
    dados = cursor.fetchall()

    # USUÁRIOS (ADMIN)
    cursor.execute("SELECT id, username, tipo FROM usuarios")
    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("dashboard.html", dados=dados, usuarios=usuarios)

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

# 🚀 RODAR LOCAL / RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)