# client/scenes/rat_race_scene.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading, random, time
from common.messages import MSG_RACE_UPDATE
from config.config import CONFIG_PARAMS

BG = "#061018"
TRACK = "#0f4c5c"
MOUSE_COLOR = "#ffd27a"

class RaceScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id

        self.race_len = CONFIG_PARAMS["RACE_LENGTH"]
        self.num_mice = CONFIG_PARAMS["RACE_NUM_MICE"]

        self.selected = None     # tu ratón elegido
        self.pos = 0
        self.running = False
        self.t = None

        self.canvas_objects = {}
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)

        tk.Label(self, text="CARRERA DE RATONES",
                 font=("Arial", 18), fg="#2ef0f0", bg=BG).pack(pady=6)

        # canvas
        self.canvas = tk.Canvas(self, width=self.race_len + 140,
                                height=50*self.num_mice,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        # dibujar pistas
        for i in range(self.num_mice):
            y = 20 + i*50
            self.canvas.create_rectangle(
                10, y-10, self.race_len+110, y+20, fill=TRACK, outline=""
            )
            label = f"m{i+1}"
            item = self.canvas.create_text(
                20, y, text="🐀", anchor="w",
                fill=MOUSE_COLOR, font=("Arial", 16)
            )
            self.canvas_objects[label] = item

        # controles
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack()

        tk.Label(ctrl, text="Elige tu ratón:", bg=BG, fg="white").pack()

        self.combo = ttk.Combobox(
            ctrl, values=[f"m{i+1}" for i in range(self.num_mice)]
        )
        self.combo.pack(pady=5)

        tk.Button(ctrl, text="Elegir y comenzar",
                  bg="#ff9a2e", command=self.choose_and_start).pack(pady=4)

        tk.Button(ctrl, text="Volver",
                  command=lambda: self.app.show_scene("MENU")).pack(pady=4)

    def choose_and_start(self):
        choice = self.combo.get()
        if not choice:
            messagebox.showwarning("Error", "Elige un ratón")
            return

        self.selected = choice
        self.pos = 0
        self.running = True

        # enviar SELECCIÓN al server
        self.net.send({
            "type": "RACE_SELECT",
            "client_id": self.client_id,
            "mouse_id": self.selected
        })

        # iniciar hilo
        self.t = threading.Thread(target=self.run_mouse, daemon=True)
        self.t.start()

    def run_mouse(self):
        while self.running and self.pos < self.race_len:
            step = random.randint(CONFIG_PARAMS["RACE_STEP_MIN"],
                                  CONFIG_PARAMS["RACE_STEP_MAX"])
            self.pos += step
            if self.pos > self.race_len:
                self.pos = self.race_len

            # mover local
            self.canvas.after(0, self.update_local)

            # mandar update
            self.net.send({
                "type": MSG_RACE_UPDATE,
                "client_id": self.client_id,
                "mouse_id": self.selected,
                "pos": self.pos
            })

            time.sleep(CONFIG_PARAMS["RACE_INTERVAL"])

        self.running = False

    def update_local(self):
        item = self.canvas_objects[self.selected]
        y = self.canvas.coords(item)[1]
        self.canvas.coords(item, 20 + self.pos, y)

    def handle_server_msg(self, msg):
        if msg.get("type") == "RACE_FINISH" and msg.get("client_id") == self.client_id:
            place = msg["your_place"]
            order = msg["ranking"]

            if place == 1:
                messagebox.showinfo("🎉 Carrera", "¡Ganaste la carrera! 🐀💨")
            else:
                messagebox.showinfo(
                    "Carrera terminada",
                    f"Quedaste en posición {place}\nRanking: {order}"
                )
