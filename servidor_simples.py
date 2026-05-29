#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
import time
from pathlib import Path

class MeuHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Log apenas erros importantes
        if '404' in str(args):
            print(f"⚠️  {args[0]}")
        elif '500' in str(args):
            print(f"❌ {args[0]}")

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        return super().do_GET()

if __name__ == "__main__":
    # Muda para o diretório do app
    diretorio = Path(__file__).parent
    os.chdir(diretorio)

    porta = 5000
    endereco = ('localhost', porta)

    print("\n" + "="*60)
    print("🚀 SERVIDOR DATACOM APP")
    print("="*60)
    print()
    print("✅ Servidor iniciado!")
    print()
    print(f"🌐 Acesse em: http://localhost:{porta}")
    print()
    print("📝 Você pode:")
    print("   1. Abrir seu navegador")
    print("   2. Digitar na barra: http://localhost:5000")
    print("   3. Pressionar ENTER")
    print()
    print("🛑 Para parar: Pressione CTRL + C")
    print()
    print("="*60 + "\n")

    # Inicia servidor
    try:
        with socketserver.TCPServer(endereco, MeuHandler) as httpd:
            print("⏳ Servidor aguardando conexões...\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Servidor encerrado")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
