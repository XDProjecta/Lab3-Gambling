# client/scenes/rat_race_scene.py
import tkinter as tk
from tkinter import ttk
from config.config import CONFIG_PARAMS
from common.messages import MSG_RACE_UPDATE
import threading, random, time

BG = "#061018"
TRACK = "#0f4c5c"
MOUSE_COLOR = "#ffd27a"

class RaceScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id
        self.num_mice = CONFIG_PARAMS["RACE_NUM_MICE"]
        self.length = CONFIG_PARAMS["RACE_LENGTH"]
        self.labels = {}
        self.positions = {f"m{i+1}": 0 for i in range(self.num_mice)}
        self.running = False
        self._threads = []
        # control de envío: enviar sólo cada N pixeles
        self._send_step = 5   # enviar cada 5 pixeles (ajusta si quieres menos ruido)
        self._sent_until = {mid: 0 for mid in self.positions.keys()}
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)
        header = tk.Label(self, text="CARRERA DE RATONES", font=("Arial", 18), bg=BG, fg="#2ef0f0")
        header.pack(pady=6)
        self.canvas = tk.Canvas(self, width=min(800, self.length+120), height=40*self.num_mice+60, bg=BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        for i in range(self.num_mice):
            y = 20 + i*40
            self.canvas.create_rectangle(10, y-2, self.length+110, y+26, fill=TRACK, outline="")
            mid = f"m{i+1}"
            lbl = self.canvas.create_text(20, y+10, text="🐀", font=("Arial", 14), anchor="w", fill=MOUSE_COLOR)
            self.labels[mid] = lbl

        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=8)
        tk.Button(ctrl, text="Iniciar (local)", command=self.start_local, bg="#ff9a2e").pack(side="left", padx=6)
        tk.Button(ctrl, text="Pausar", command=self.pause_local, bg="#ff5c7a").pack(side="left", padx=6)
        tk.Button(ctrl, text="Enviar snapshot", command=self.send_snapshot, bg="#2ef0f0").pack(side="left", padx=6)
        tk.Button(ctrl, text="Volver", command=lambda: self.app.show_scene("MENU")).pack(side="left", padx=6)

    def start_local(self):
        if self.running:
            return
        self.running = True
        self._threads = []
        for mid in list(self.labels.keys()):
            t = threading.Thread(target=self._mouse_thread, args=(mid,), daemon=True)
            t.start()
            self._threads.append(t)

    def _mouse_thread(self, mid):
        while self.running:
            # comportamiento local visual
            step = random.randint(CONFIG_PARAMS["RACE_STEP_MIN"], CONFIG_PARAMS["RACE_STEP_MAX"])
            self.positions[mid] += step
            pos = min(self.positions[mid], self.length)
            self.canvas.after(0, self.canvas.coords, self.labels[mid], 20+pos, self.canvas.coords(self.labels[mid])[1])

            # si alcanzó la meta, enviar notificación final y dejar de enviar futuras posiciones para este mid
            if pos >= self.length:
                # enviar última posición final
                if self.net and getattr(self.net, "connected", False):
                    try:
                        self.net.send({"type": MSG_RACE_UPDATE, "client_id": self.client_id, "mouse_id": mid, "pos": pos, "finish": True})
                    except:
                        pass
                # marcar como enviado hasta el final (no enviar más)
                self._sent_until[mid] = pos
                # romper el loop para ese ratón (sigue existiendo la visual)
                break

            # throttle: enviar solo si avanzó _send_step pixeles desde el último envío
            if pos - self._sent_until.get(mid, 0) >= self._send_step:
                if self.net and getattr(self.net, "connected", False):
                    try:
                        self.net.send({"type": MSG_RACE_UPDATE, "client_id": self.client_id, "mouse_id": mid, "pos": pos})
                        self._sent_until[mid] = pos
                    except Exception:
                        pass

            time.sleep(CONFIG_PARAMS["RACE_INTERVAL"])

    def pause_local(self):
        self.running = False

    def send_snapshot(self):
        if self.net and getattr(self.net, "connected", False):
            for mid, pos in self.positions.items():
                try:
                    self.net.send({"type": MSG_RACE_UPDATE, "client_id": self.client_id, "mouse_id": mid, "pos": pos})
                except:
                    pass
