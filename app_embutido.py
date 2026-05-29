#!/usr/bin/env python3
import sys
import subprocess

# Tenta importar webview
try:
    import webview
except ImportError:
    print("📦 Instalando pywebview...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview", "-q"])
    import webview

from pathlib import Path

if __name__ == "__main__":
    # Caminho do HTML
    html_path = Path(__file__).parent / "index.html"
    html_url = html_path.as_uri()

    print("=" * 60)
    print("🚀 DATACOM APP - JANELA DESKTOP")
    print("=" * 60)
    print()
    print("✅ Abrindo app...")
    print()

    # Cria janela com o app embutido
    webview.create_window(
        title='Datacom App',
        url=html_url,
        width=1400,
        height=900,
        min_size=(800, 600),
        background_color='#0b0e0d'
    )

    # Inicia a janela
    webview.start(debug=False)

    print("✅ App fechado")
