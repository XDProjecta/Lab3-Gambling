# server/gui_server.py
"""
GUI del servidor (Tkinter).
Permite iniciar/detener servidor y ver logs (quita códigos ANSI al mostrar en la ventana).
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import re
import builtins
from server.server import Server

# regex para eliminar secuencias ANSI (ej. \x1b[...m)
ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Servidor - ProyectoCasino")
        self.server = Server()
        self._orig_print = builtins.print  # guardar print original
        self._override_print()
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Servidor - ProyectoCasino", font=("Arial", 14)).pack(side="left")

        btns = ttk.Frame(top)
        btns.pack(side="right")

        self.start_btn = ttk.Button(btns, text="Iniciar servidor", command=self.start_server)
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = ttk.Button(btns, text="Detener servidor", command=self.stop_server, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        self.log = scrolledtext.ScrolledText(self.root, height=24)
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

        self.status = ttk.Label(self.root, text="Servidor detenido")
        self.status.pack(fill="x")

    def _override_print(self):
        # Redirige print para que pinte en la GUI (limpiando códigos ANSI)
        def print_override(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            clean = ANSI_RE.sub('', text)
            try:
                # insertar en widget (thread-safe desde cualquier hilo)
                self.log.insert("end", clean + "\n")
                self.log.see("end")
            except Exception:
                pass
            # también continuar enviando al stdout original (con colores si hay)
            try:
                self._orig_print(text, **kwargs)
            except Exception:
                pass

        builtins.print = print_override

    def start_server(self):
        # arrancar servidor en hilo
        threading.Thread(target=self.server.start, daemon=True).start()
        self.status.config(text=f"Escuchando en {self.server.host}:{self.server.port}")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop_server(self):
        self.server.stop()
        self.status.config(text="Servidor detenido")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
