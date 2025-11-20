# client/scenes/rat_race_scene.py
import tkinter as tk
from tkinter import ttk
from config.config import CONFIG_PARAMS
from common.messages import MSG_RACE_UPDATE
import threading, random, time

class RaceScene(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id
        self.num_mice = CONFIG_PARAMS["RACE_NUM_MICE"]
        self.length = CONFIG_PARAMS["RACE_LENGTH"]
        self.labels = {}
        self.positions = {f"m{i+1}": 0 for i in range(self.num_mice)}
        self.running = False
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)
        ttk.Label(self, text="Carrera de Ratones", font=("Arial", 18)).pack(pady=8)
        self.canvas = tk.Canvas(self, width=self.length+120, height=40*self.num_mice+40, bg="#fffaf0")
        self.canvas.pack(padx=8, pady=8)
        for i in range(self.num_mice):
            mid = f"m{i+1}"
            y = 10 + i*40
            lbl = tk.Label(self.canvas, text="🐀", font=("Arial", 18))
            lbl.place(x=10, y=y)
            self.labels[mid] = lbl

        ctrl = ttk.Frame(self)
        ctrl.pack()
        ttk.Button(ctrl, text="Iniciar (local)", command=self.start_local).pack(side="left", padx=6)
        ttk.Button(ctrl, text="Pausar", command=self.pause_local).pack(side="left", padx=6)
        ttk.Button(ctrl, text="Volver", command=lambda: self.app.show_scene("MENU")).pack(side="left", padx=6)

    def start_local(self):
        if self.running:
            return
        self.running = True
        for mid in list(self.labels.keys()):
            t = threading.Thread(target=self._mouse_thread, args=(mid,), daemon=True)
            t.start()

    def _mouse_thread(self, mid):
        while self.running:
            step = random.randint(CONFIG_PARAMS["RACE_STEP_MIN"], CONFIG_PARAMS["RACE_STEP_MAX"])
            self.positions[mid] += step
            pos = min(self.positions[mid], self.length)
            # mover etiqueta (usar after para thread-safe)
            self.canvas.after(0, self.labels[mid].place, {"x": 10+pos, "y": self.labels[mid].winfo_y()})
            # enviar al servidor
            if self.net and self.net.connected:
                self.net.send({"type": MSG_RACE_UPDATE, "client_id": self.client_id, "mouse_id": mid, "pos": pos})
            time.sleep(CONFIG_PARAMS["RACE_INTERVAL"])

    def pause_local(self):
        self.running = False
