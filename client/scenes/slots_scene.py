# client/scenes/slots_scene.py
import tkinter as tk
from tkinter import ttk
import random
from common.messages import MSG_SLOTS_SPIN, MSG_SLOTS_RESULT
from config.config import CONFIG_PARAMS

# paleta retro
BG = "#071018"
PANEL = "#26003b"
TEXT_NEON = "#ff55ff"
ACCENT = "#00eaff"

class SlotsScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.net = getattr(app, "net", None)
        self.client_id = getattr(app, "client_id", "client-unknown")
        # seguridad: garantizar tipos correctos
        self.symbols = CONFIG_PARAMS.get("SLOTS_SYMBOLS", ["🍒", "🍋", "🔔"])
        reels_val = CONFIG_PARAMS.get("SLOTS_REELS", 3)
        try:
            self.reels = int(reels_val)
            if self.reels < 1:
                self.reels = 3
        except Exception:
            self.reels = 3

        self.reel_items = []   # ids de canvas para cada reel
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)
        title = tk.Label(self, text="SLOTS", font=("Arial Black", 24), fg="#ff9a9f", bg=BG)
        title.pack(pady=12)

        # marco tipo "máquina"
        box = tk.Frame(self, bg=PANEL, bd=6, relief="ridge")
        box.pack(pady=12)

        # canvas donde van los símbolos
        self.canvas = tk.Canvas(box, width=420, height=180, bg="#10061a", highlightthickness=0)
        self.canvas.pack()

        # crear los textos (centrados por columna)
        self.reel_items = []
        spacing = 420 // max(1, self.reels)
        start_x = spacing // 2
        for i in range(self.reels):
            x = start_x + i * spacing
            sym = random.choice(self.symbols)
            tid = self.canvas.create_text(x, 90, text=sym, font=("Arial", 48), fill=TEXT_NEON)
            self.reel_items.append(tid)

        # botones
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=8)

        spin_btn = tk.Button(ctrl, text="SPIN", font=("Arial Black", 18),
                             fg=ACCENT, bg="#00374d", activebackground="#005f80",
                             width=10, command=self.spin)
        spin_btn.pack(side="left", padx=8)

        tk.Button(ctrl, text="Volver", font=("Arial", 12),
                  command=lambda: self.app.show_scene("MENU")).pack(side="left", padx=8)

        # resultado
        self.result_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.result_var, font=("Arial", 12), fg=ACCENT, bg=BG).pack(pady=6)

    def spin(self):
        # enviar petición al servidor (si hay conexión)
        if self.net and getattr(self.net, "connected", False):
            try:
                self.net.send({"type": MSG_SLOTS_SPIN, "client_id": self.client_id})
            except Exception as e:
                print("[SLOTS] Error enviando SPIN:", e)

        # animación local, luego queda a la espera de respuesta del servidor
        self._animate_local(10)

    def _animate_local(self, steps):
        # animación rápida (no bloqueante)
        if steps <= 0:
            return
        for tid in self.reel_items:
            sym = random.choice(self.symbols)
            # actualizamos texto y color para efecto neón
            self.canvas.itemconfig(tid, text=sym, fill=random.choice([TEXT_NEON, ACCENT, "#ffdd55"]))
        # programar siguiente frame
        self.after(80, lambda: self._animate_local(steps - 1))

    def handle_server_msg(self, msg):
        # recibido del servidor: resultado final
        try:
            if msg.get("type") == MSG_SLOTS_RESULT and msg.get("client_id") == self.client_id:
                result = msg.get("result", [])
                win = msg.get("win", 0)

                # actualizar canvas con el resultado exacto (si el servidor devolvió menos, rellenar)
                for i in range(self.reels):
                    sym = result[i] if i < len(result) else random.choice(self.symbols)
                    try:
                        tid = self.reel_items[i]
                        self.canvas.itemconfig(tid, text=sym, fill=TEXT_NEON)
                    except Exception:
                        pass

                # mostrar premio/estado
                self.result_var.set(f"Resultado: {' '.join(result)}   Premio: {win}")
        except Exception as e:
            print("[SLOTS] Error manejando mensaje del servidor:", e)
