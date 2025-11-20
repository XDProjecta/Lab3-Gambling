# client/scenes/slots_scene.py
import tkinter as tk
from tkinter import ttk
from common.messages import MSG_SLOTS_SPIN, MSG_SLOTS_RESULT
from config.config import CONFIG_PARAMS

class SlotsScene(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id
        self.symbols = CONFIG_PARAMS["SLOTS_SYMBOLS"]
        self.reels = CONFIG_PARAMS["SLOTS_REELS"]
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)
        ttk.Label(self, text="SLOTS - Tragamonedas", font=("Arial", 18)).pack(pady=8)
        self.canvas = tk.Canvas(self, width=400, height=160, bg="#fff0f5")
        self.canvas.pack(padx=8, pady=8)
        self.reel_texts = []
        for i in range(self.reels):
            t = self.canvas.create_text(80 + i*110, 70, text=self.symbols[i % len(self.symbols)], font=("Arial", 40))
            self.reel_texts.append(t)

        btns = ttk.Frame(self)
        btns.pack(pady=8)
        ttk.Button(btns, text="Spin", command=self.spin).pack(side="left", padx=6)
        ttk.Button(btns, text="Volver", command=lambda: self.app.show_scene("MENU")).pack(side="left", padx=6)
        self.result_var = tk.StringVar()
        ttk.Label(self, textvariable=self.result_var, font=("Arial", 14)).pack(pady=6)

    def spin(self):
        if self.net and self.net.connected:
            self.net.send({"type": MSG_SLOTS_SPIN, "client_id": self.client_id})
        # animación rápida local
        self._animate(8)

    def _animate(self, steps):
        import random
        if steps <= 0:
            return
        for i, t in enumerate(self.reel_texts):
            sym = random.choice(self.symbols)
            self.canvas.itemconfig(t, text=sym)
        self.after(80, lambda: self._animate(steps-1))

    def handle_server_msg(self, msg):
        if msg.get("type") == MSG_SLOTS_RESULT and msg.get("client_id") == self.client_id:
            res = msg.get("result")
            win = msg.get("win", 0)
            for i, sym in enumerate(res):
                self.canvas.itemconfig(self.reel_texts[i], text=sym)
            self.result_var.set(f"Resultado: {' '.join(res)} Premio: {win}")
