from app import app
import webview

webview.create_window("Sistema de Controle", app)
webview.start()