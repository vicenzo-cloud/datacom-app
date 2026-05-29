#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
from pathlib import Path

# Instala tkhtmlview se não tiver
try:
    from tkhtmlview import HTML
except ImportError:
    print("📦 Instalando tkhtmlview...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tkhtmlview", "-q"])
    from tkhtmlview import HTML

class AppCompleto:
    def __init__(self, root):
        self.root = root
        self.root.title("Datacom App")
        self.root.geometry("1400x900")
        self.root.minsize(800, 600)
        self.root.configure(bg="#0b0e0d")

        # Lê o HTML
        html_path = Path(__file__).parent / "index.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            self.html_content = f.read()

        # Frame principal
        frame = tk.Frame(root, bg="#0b0e0d")
        frame.pack(fill=tk.BOTH, expand=True)

        # Widget HTML
        try:
            self.html_widget = HTML(frame, bg="#0b0e0d")
            self.html_widget.pack(fill=tk.BOTH, expand=True)

            # Carrega o HTML
            self.html_widget.set_html(self.html_content)
        except Exception as e:
            label = tk.Label(
                frame,
                text=f"❌ Erro ao renderizar HTML:\n{str(e)}",
                font=("Arial", 12),
                bg="#0b0e0d",
                fg="#ff5252"
            )
            label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

    def fechar(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppCompleto(root)
    root.mainloop()
