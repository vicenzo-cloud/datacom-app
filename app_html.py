#!/usr/bin/env python3
import tkinter as tk
import http.server
import socketserver
import os
import threading
import socket
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen
from tkinter import scrolledtext

class ServidorHTTP:
    def __init__(self, porta_inicial=5000):
        self.porta = self.encontrar_porta(porta_inicial)
        self.thread = None
        self.servidor = None

    def encontrar_porta(self, inicial):
        for porta in range(inicial, inicial + 100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', porta))
                sock.close()
                return porta
            except OSError:
                continue
        return inicial

    def iniciar(self):
        os.chdir(Path(__file__).parent)

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_GET(self):
                if self.path == '/' or self.path == '':
                    self.path = '/index.html'
                return super().do_GET()

        self.servidor = socketserver.TCPServer(("localhost", self.porta), Handler)
        self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.thread.start()

    def parar(self):
        if self.servidor:
            self.servidor.shutdown()

class AppDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("Datacom App")
        self.root.geometry("1400x900")
        self.root.minsize(800, 600)
        self.root.configure(bg="#0b0e0d")

        # Inicia servidor
        self.servidor = ServidorHTTP()
        self.servidor.iniciar()

        # Frame principal
        self.frame_main = tk.Frame(root, bg="#131716")
        self.frame_main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        self.titulo = tk.Label(
            self.frame_main,
            text="🚀 Datacom App",
            font=("Arial", 24, "bold"),
            bg="#131716",
            fg="#00d48a"
        )
        self.titulo.pack(pady=20)

        # Status
        self.status = tk.Label(
            self.frame_main,
            text=f"✅ Servidor rodando na porta {self.servidor.porta}",
            font=("Arial", 12),
            bg="#131716",
            fg="#00d48a"
        )
        self.status.pack(pady=10)

        # Botão
        self.botao = tk.Button(
            self.frame_main,
            text="📱 Carregar App",
            font=("Arial", 12, "bold"),
            bg="#00d48a",
            fg="#0b0e0d",
            padx=30,
            pady=15,
            command=self.carregar_app
        )
        self.botao.pack(pady=20)

        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

    def carregar_app(self):
        # Limpa interface antiga
        self.titulo.pack_forget()
        self.status.pack_forget()
        self.botao.pack_forget()

        # Nova label
        label = tk.Label(
            self.frame_main,
            text="⏳ Carregando...",
            font=("Arial", 14),
            bg="#131716",
            fg="#00d48a"
        )
        label.pack(pady=20)
        self.root.update()

        # Tenta abrir no navegador
        import webbrowser
        url = f"http://localhost:{self.servidor.porta}"

        label.config(text=f"✅ App aberto em:\n{url}\n\nVocê pode continuar usando a janela ou acessar pelo navegador.")
        webbrowser.open(url)

    def fechar(self):
        self.servidor.parar()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppDesktop(root)
    root.mainloop()
