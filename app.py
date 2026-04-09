from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
from datetime import datetime
import os
import sys

app = Flask(__name__)
app.secret_key = "123"

# 🔥 FUNÇÃO PARA CAMINHO CORRETO NO .EXE
def caminho_arquivo(nome):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), nome)
    return nome

# 📁 ARQUIVO
arquivo = caminho_arquivo("controle.xlsx")

# 🧠 CRIAR PLANILHA SE NÃO EXISTIR
if not os.path.exists(arquivo):
    df = pd.DataFrame(columns=["ID", "Nome", "Telefone", "Material", "Saída", "Devolução"])
    df.to_excel(arquivo, index=False)

# 🔐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        senha = request.form["senha"]

        if user == "admin" and senha == "1234":
            session["user"] = user
            return redirect("/dashboard")

    return render_template("login.html")

# 📊 DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    df = pd.read_excel(arquivo)

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        material = request.form["material"]

        novo_id = 1 if df.empty else df["ID"].max() + 1

        df.loc[len(df)] = [
            novo_id,
            nome,
            telefone,
            material,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            "PENDENTE"
        ]

        df.to_excel(arquivo, index=False)
        return redirect("/dashboard")

    dados = df.values.tolist()
    return render_template("dashboard.html", dados=dados)

# 🔁 DEVOLVER
@app.route("/devolver/<int:id>")
def devolver(id):
    df = pd.read_excel(arquivo)

    df.loc[df["ID"] == id, "Devolução"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    df.to_excel(arquivo, index=False)
    return redirect("/dashboard")

# 🗑️ EXCLUIR
@app.route("/excluir/<int:id>")
def excluir(id):
    df = pd.read_excel(arquivo)
    df = df[df["ID"] != id]
    df.to_excel(arquivo, index=False)
    return redirect("/dashboard")

# 📄 PÁGINA RELATÓRIO
@app.route("/relatorio")
def relatorio():
    if "user" not in session:
        return redirect("/")
    return render_template("relatorio.html")

# 📥 DOWNLOAD RELATÓRIO (CORRIGIDO)
@app.route("/baixar_relatorio")
def baixar_relatorio():
    caminho_relatorio = caminho_arquivo("relatorio.xlsx")

    df = pd.read_excel(arquivo)
    df.to_excel(caminho_relatorio, index=False)

    return send_file(caminho_relatorio, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)