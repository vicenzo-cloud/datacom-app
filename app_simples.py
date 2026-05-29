import tkinter as tk
from tkinter import ttk
import webbrowser
import subprocess
import sys
import os
from pathlib import Path
import threading
import time

# Instala pywebview se não tiver
def instalar_dependencias():
    try:
        import webview
    except ImportError:
        print("Instalando pywebview...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview", "-q"])

# Tenta usar webview
def abrir_como_janela():
    try:
        instalar_dependencias()
        import webview

        html_path = Path(__file__).parent / "index.html"
        html_url = html_path.as_uri()

        webview.create_window(
            title='Datacom App',
            url=html_url,
            width=1400,
            height=900,
            min_size=(800, 600),
            background_color='#0b0e0d'
        )
        webview.start(debug=False)
    except Exception as e:
        print(f"Erro ao abrir como janela: {e}")
        abrir_no_navegador()

# Se falhar, abre no navegador
def abrir_no_navegador():
    html_path = Path(__file__).parent / "index.html"
    webbrowser.open(html_path.as_uri())

# Executa em thread para não bloquear
if __name__ == "__main__":
    print("Iniciando Datacom App...")
    abrir_como_janela()
