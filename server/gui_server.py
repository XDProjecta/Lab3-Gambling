import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from server.server import Server

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Servidor - ProyectoCasino")

        self.server = Server()
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Servidor - ProyectoCasino", font=("Arial", 14)).pack(side="left")

        btns = ttk.Frame(top)
        btns.pack(side="right")

        self.start_btn = ttk.Button(btns, text="Iniciar servidor", command=self.start_server)
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = ttk.Button(btns, text="Detener servidor",
                                   command=self.stop_server, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        self.log = scrolledtext.ScrolledText(self.root, height=20)
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

        self.status = ttk.Label(self.root, text="Servidor detenido")
        self.status.pack(fill="x")

        # REDIRECTION DE PRINT
        import builtins
        self._old_print = print

        def new_print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            try:
                self.log.insert("end", msg + "\n")
                self.log.see("end")
            except:
                pass
            self._old_print(*args, **kwargs)

        builtins.print = new_print

    def start_server(self):
        threading.Thread(target=self.server.start, daemon=True).start()
        self.status.config(text=f"Escuchando en {self.server.host}:{self.server.port}")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop_server(self):
        self.server.stop()
        self.status.config(text="Servidor detenido")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
