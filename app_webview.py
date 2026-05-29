#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    import webview
except ImportError:
    print("Instalando webview...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview", "-q"])
    import webview

from pathlib import Path

if __name__ == "__main__":
    html_path = Path(__file__).parent / "index.html"
    html_url = html_path.as_uri()

    print("=" * 60)
    print("DATACOM APP")
    print("=" * 60)
    print("Abrindo app...")

    webview.create_window(
        title='Datacom App',
        url=html_url,
        width=1400,
        height=900,
        min_size=(800, 600),
        background_color='#0b0e0d'
    )

    webview.start(debug=False)
    print("App fechado")
