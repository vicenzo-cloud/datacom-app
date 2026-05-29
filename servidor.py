from flask import Flask, render_template_string, static_file
import os
import sys
from pathlib import Path

app = Flask(__name__, static_folder=None)

# Carrega o HTML
html_path = Path(__file__).parent / "index.html"
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

@app.route('/')
def index():
    return render_template_string(html_content)

@app.errorhandler(404)
def not_found(error):
    return "Arquivo não encontrado", 404

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SERVIDOR DATACOM APP")
    print("="*60)
    print()
    print("✅ Servidor iniciado com sucesso!")
    print()
    print("🌐 Acesse em:  http://localhost:5000")
    print()
    print("📍 Abra seu navegador e digite na barra de endereço:")
    print("   http://localhost:5000")
    print()
    print("🛑 Para parar o servidor:")
    print("   Pressione CTRL + C")
    print()
    print("="*60 + "\n")

    # Inicia o servidor
    app.run(
        host='localhost',
        port=5000,
        debug=False,
        use_reloader=False
    )
