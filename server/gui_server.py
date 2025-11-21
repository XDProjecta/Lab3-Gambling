# gui_server.py
"""
GUI del Servidor
----------------
Este archivo muestra:
- Información del servidor
- Botón para iniciar / detener
- Consola de eventos
- Vista gráfica del estado de la carrera de ratones

NO MANEJA LA LÓGICA DEL JUEGO.
Eso pasa es en:
    server/server.py
    server/games/*
"""

import tkinter as tk
from tkinter import ttk
from server.server import GameServer
from config.config import CONFIG_PARAMS


class ServerGUI:
    def __init__(self):
        """Inicializa la ventana gráfica del servidor."""
        self.root = tk.Tk()
        self.root.title("Casino - Servidor")
        self.root.geometry("900x500")

        # Servidor real (TCP)
        self.server = GameServer(on_event=self.log)

        self.build()

    def build(self):
        """Interfaz gráfica: botones + log + panel de carrera."""
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        # Botones
        ctrl = ttk.Frame(frame)
        ctrl.pack(pady=10)

        ttk.Button(ctrl, text="Iniciar Servidor",
                   command=self.start).pack(side="left", padx=10)

        ttk.Button(ctrl, text="Detener",
                   command=self.stop).pack(side="left", padx=10)

        # LOG debajo
        self.log_box = tk.Text(frame, height=10)
        self.log_box.pack(fill="x", padx=10, pady=10)

        # Area donde se dibuja la carrera del lado del servidor
        self.canvas = tk.Canvas(frame, width=800, height=260,
                                bg="#061018")
        self.canvas.pack(padx=10, pady=10)

        # Dibujar pista inicial
        num_mice = CONFIG_PARAMS["RACE_NUM_MICE"]
        for i in range(num_mice):
            y = 30 + i * 50
            self.canvas.create_rectangle(10, y - 10,
                                         780, y + 20,
                                         fill="#112233")

            self.canvas.create_text(20, y,
                                    text=f"m{i+1}",
                                    fill="#ffcc44",
                                    anchor="w")

    def log(self, msg):
        """Escribe en el log interno del servidor."""
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def start(self):
        """Arranca el servidor en un hilo."""
        self.server.start()
        self.log("Servidor iniciado.")

    def stop(self):
        """Detiene el servidor."""
        self.server.stop()
        self.log("Servidor detenido.")

    def update_race(self, positions):
        """
        El GameServer llama esto para mostrar posiciones en la GUI.
        positions es un diccionario: { "m1": pos, "m2": pos, ... }
        """
        for m, pos in positions.items():
            # Buscar el texto m1, m2, m3...
            # Nota: esto es una aproximación simple
            items = self.canvas.find_withtag("all")
            for item in items:
                if self.canvas.type(item) == "text":
                    if self.canvas.itemcget(item, "text") == m:
                        y = self.canvas.coords(item)[1]
                        self.canvas.coords(item, 20 + pos, y)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = ServerGUI()
    gui.run()
