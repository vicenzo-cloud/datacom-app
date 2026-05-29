#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import http.server
import socketserver
import os
import threading
import socket
from pathlib import Path

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
        frame = tk.Frame(root, bg="#131716")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        titulo = tk.Label(
            frame,
            text="🚀 Datacom App",
            font=("Arial", 24, "bold"),
            bg="#131716",
            fg="#00d48a"
        )
        titulo.pack(pady=20)

        # Status
        status = tk.Label(
            frame,
            text=f"✅ Servidor rodando na porta {self.servidor.porta}",
            font=("Arial", 12),
            bg="#131716",
            fg="#00d48a"
        )
        status.pack(pady=10)

        # Info
        info = tk.Label(
            frame,
            text="Clique no botão para carregar o app",
            font=("Arial", 10),
            bg="#131716",
            fg="#6b7c72"
        )
        info.pack(pady=10)

        # Botão
        botao = tk.Button(
            frame,
            text="📱 Carregar App",
            font=("Arial", 12, "bold"),
            bg="#00d48a",
            fg="#0b0e0d",
            padx=30,
            pady=15,
            command=self.carregar_app
        )
        botao.pack(pady=20)

        # Frame para o conteúdo
        self.frame_conteudo = tk.Frame(frame, bg="#0b0e0d", height=400)
        self.frame_conteudo.pack(fill=tk.BOTH, expand=True, pady=20)

        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

    def carregar_app(self):
        self.frame_conteudo.destroy()

        # Label informando que deve abrir no navegador
        label = tk.Label(
            self.root,
            text="App carregado! Use CTRL+clique ou clique com botão direito para acessar funcionalidades completas.\n\nOu acesse no navegador: http://localhost:" + str(self.servidor.porta),
            font=("Arial", 11),
            bg="#131716",
            fg="#e2e8e4",
            justify=tk.CENTER
        )
        label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def fechar(self):
        self.servidor.parar()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppDesktop(root)
    root.mainloop()
