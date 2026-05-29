import sys
import os
import threading
import time
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket

# Encontra uma porta disponível
def encontrar_porta_disponivel(porta_inicial=5000):
    for porta in range(porta_inicial, porta_inicial + 100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', porta))
            sock.close()
            return porta
        except OSError:
            continue
    return porta_inicial

# Handler customizado para servir arquivos
class MeuHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silencia os logs

    def do_GET(self):
        # Se for raiz, serve index.html
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

# Inicia servidor em thread
def iniciar_servidor(porta, diretorio):
    os.chdir(diretorio)
    servidor = HTTPServer(('localhost', porta), MeuHandler)
    print(f"🌐 Servidor rodando em http://localhost:{porta}")
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    return servidor

# Main
if __name__ == "__main__":
    diretorio = Path(__file__).parent
    porta = encontrar_porta_disponivel()

    print("=" * 50)
    print("🚀 Datacom App iniciando...")
    print("=" * 50)

    # Inicia servidor
    servidor = iniciar_servidor(porta, diretorio)

    # Aguarda um pouco para garantir que servidor está pronto
    time.sleep(1)

    # Abre no navegador
    url = f"http://localhost:{porta}"
    print(f"📍 Abrindo em {url}")
    webbrowser.open(url)

    print("✅ App aberto!")
    print("💡 Feche esta janela para encerrar o app")
    print("=" * 50)

    # Mantém rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ App fechado")
