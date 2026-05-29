import tkinter as tk
from tkinter import ttk
import http.server
import socketserver
import os
import threading
import time
from pathlib import Path
import webbrowser
import socket

class AppWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Datacom App")
        self.root.geometry("1400x900")
        self.root.minsize(800, 600)

        # Define cores
        self.root.configure(bg="#0b0e0d")

        # Servidor
        self.servidor = None
        self.thread_servidor = None
        self.porta = self.encontrar_porta_disponivel(5000)

        # Frame principal
        self.frame_principal = tk.Frame(root, bg="#131716")
        self.frame_principal.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        self.titulo = tk.Label(
            self.frame_principal,
            text="🚀 Datacom App",
            font=("Arial", 24, "bold"),
            bg="#131716",
            fg="#00d48a"
        )
        self.titulo.pack(pady=20)

        # Status
        self.status_label = tk.Label(
            self.frame_principal,
            text="Iniciando servidor...",
            font=("Arial", 12),
            bg="#131716",
            fg="#e2e8e4"
        )
        self.status_label.pack(pady=10)

        # Botão abrir
        self.botao_abrir = tk.Button(
            self.frame_principal,
            text="🌐 Abrir App no Navegador",
            font=("Arial", 12, "bold"),
            bg="#00d48a",
            fg="#0b0e0d",
            padx=20,
            pady=10,
            command=self.abrir_navegador,
            state=tk.DISABLED
        )
        self.botao_abrir.pack(pady=20)

        # Info
        self.info_label = tk.Label(
            self.frame_principal,
            text="",
            font=("Arial", 10),
            bg="#131716",
            fg="#6b7c72"
        )
        self.info_label.pack(pady=10)

        # Inicia servidor em thread
        self.iniciar_servidor()

    def encontrar_porta_disponivel(self, porta_inicial=5000):
        for porta in range(porta_inicial, porta_inicial + 100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', porta))
                sock.close()
                return porta
            except OSError:
                continue
        return porta_inicial

    def iniciar_servidor(self):
        self.thread_servidor = threading.Thread(target=self.rodar_servidor, daemon=True)
        self.thread_servidor.start()

    def rodar_servidor(self):
        try:
            diretorio = Path(__file__).parent
            os.chdir(diretorio)

            class MeuHandler(http.server.SimpleHTTPRequestHandler):
                def log_message(self, format, *args):
                    pass

                def do_GET(self):
                    if self.path == '/' or self.path == '':
                        self.path = '/index.html'
                    return super().do_GET()

            with socketserver.TCPServer(("localhost", self.porta), MeuHandler) as httpd:
                self.atualizar_status("✅ Servidor iniciado!", "#00d48a", True)
                httpd.serve_forever()
        except Exception as e:
            self.atualizar_status(f"❌ Erro: {e}", "#ff5252", False)

    def atualizar_status(self, texto, cor, habilitar_botao):
        self.root.after(0, lambda: self._atualizar_ui(texto, cor, habilitar_botao))

    def _atualizar_ui(self, texto, cor, habilitar_botao):
        self.status_label.config(text=texto, fg=cor)
        self.info_label.config(text=f"🌐 http://localhost:{self.porta}")

        if habilitar_botao:
            self.botao_abrir.config(state=tk.NORMAL)
        else:
            self.botao_abrir.config(state=tk.DISABLED)

    def abrir_navegador(self):
        webbrowser.open(f"http://localhost:{self.porta}")
        self.status_label.config(text="✅ Navegador aberto!", fg="#00d48a")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppWindow(root)
    root.mainloop()
