# client/scenes/slots_scene.py
"""
SlotsScene
----------
Simula una máquina tragamonedas.

FUNCIONAMIENTO:
- El jugador hace click en SPIN
- Se envía un mensaje SLOTS_SPIN al servidor
- Mientras llega la respuesta, la escena reproduce una animación local
- El servidor responde con:
    { result: ["⭐","⭐","⭐"], win: 100 }
- Se muestran los símbolos reales y un mensaje de premio
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
from common.messages import MSG_SLOTS_SPIN, MSG_SLOTS_RESULT
from config.config import CONFIG_PARAMS

# Colores estilo retro
BG = "#071018"
PANEL = "#26003b"
TEXT_NEON = "#ff55ff"
ACCENT = "#00eaff"


class SlotsScene(tk.Frame):
    def __init__(self, parent, app):
        """
        parent: frame contenedor
        app: acceso a red, id, show_scene()

        Atributos:
        - symbols: lista de símbolos configurada en CONFIG
        - reels: cantidad de columnas
        - reel_items: referencias a los objetos gráfics (textos) del canvas
        """
        super().__init__(parent, bg=BG)

        self.app = app
        self.net = getattr(app, "net", None)
        self.client_id = getattr(app, "client_id", "client-unknown")

        # Símbolos desde config
        self.symbols = CONFIG_PARAMS.get(
            "SLOTS_SYMBOLS", ["🍒", "🍋", "🔔"]
        )

        # Número de carretes
        reels_val = CONFIG_PARAMS.get("SLOTS_REELS", 3)
        try:
            self.reels = int(reels_val)
            if self.reels < 1:
                self.reels = 3
        except:
            self.reels = 3

        self.reel_items = []
        self.build()

    def build(self):
        """Construcción de la interfaz gráfica del juego."""
        self.pack(fill="both", expand=True)

        # Título
        title = tk.Label(self, text="SLOTS",
                         font=("Arial Black", 24),
                         fg="#ff9a9f", bg=BG)
        title.pack(pady=12)

        # Marco que contiene el canvas de la máquina
        box = tk.Frame(self, bg=PANEL, bd=6, relief="ridge")
        box.pack(pady=12)

        # Canvas donde se dibujan los símbolos
        self.canvas = tk.Canvas(box, width=420, height=180,
                                bg="#10061a", highlightthickness=0)
        self.canvas.pack()

        # Crear símbolos iniciales
        spacing = 420 // max(1, self.reels)
        start_x = spacing // 2

        for i in range(self.reels):
            x = start_x + i * spacing
            sym = random.choice(self.symbols)

            tid = self.canvas.create_text(
                x, 90,
                text=sym,
                font=("Arial", 48),
                fill=TEXT_NEON
            )
            self.reel_items.append(tid)

        # Controles inferiores
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=8)

        spin_btn = tk.Button(
            ctrl, text="SPIN",
            font=("Arial Black", 18),
            fg=ACCENT,
            bg="#00374d",
            activebackground="#005f80",
            width=10,
            command=self.spin_slots
        )
        spin_btn.pack(side="left", padx=8)

        tk.Button(ctrl, text="Volver",
                  font=("Arial", 12),
                  command=lambda: self.app.show_scene("MENU")).pack(side="left", padx=8)

        # Etiqueta de resultado
        self.result_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.result_var,
                 font=("Arial", 12),
                 fg=ACCENT, bg=BG).pack(pady=6)

    # ---------------------------------------------------------
    # LOGICA DEL SPIN
    # ---------------------------------------------------------

    def spin_slots(self):
        """
        Inicia un spin REAL.
        Se envía mensaje al servidor, y mientras llega la respuesta,
        mostramos una animación rápida local.
        """
        if self.net and getattr(self.net, "connected", False):
            self.net.send({
                "type": MSG_SLOTS_SPIN,
                "client_id": self.client_id
            })

        # animación visual temporal
        self._animate_local(10)

    def _animate_local(self, steps):
        """
        Reproduce animación visual simple: cambia símbolos rápidamente.
        No afecta el resultado real.
        """
        if steps <= 0:
            return

        for tid in self.reel_items:
            sym = random.choice(self.symbols)
            self.canvas.itemconfig(
                tid, text=sym,
                fill=random.choice([TEXT_NEON, ACCENT, "#ffdd55"])
            )

        self.after(80, lambda: self._animate_local(steps - 1))

    # ---------------------------------------------------------
    # MANEJO DE MENSAJES DEL SERVIDOR
    # ---------------------------------------------------------

    def handle_server_msg(self, msg):
        """
        Maneja el mensaje del servidor con el resultado real del spin.
        Formato esperado:
        {
            type: "SLOTS_RESULT",
            client_id: "...",
            result: [...],
            win: <int>
        }
        """
        try:
            if msg.get("type") == MSG_SLOTS_RESULT and msg.get("client_id") == self.client_id:

                result = msg.get("result", [])
                win = msg.get("win", 0)

                # Mostrar símbolos exactos del servidor
                for i in range(self.reels):
                    sym = result[i] if i < len(result) else random.choice(self.symbols)
                    tid = self.reel_items[i]
                    self.canvas.itemconfig(tid, text=sym, fill=TEXT_NEON)

                # Texto de resultado
                self.result_var.set(
                    f"Resultado: {' '.join(result)}    Premio: {win}"
                )

                # Popup de victoria
                if win > 0:
                    messagebox.showinfo("🎰 Slots", f"¡Ganaste {win} monedas!")
                else:
                    messagebox.showinfo("🎰 Slots", "No ganaste nada 😢")

        except Exception as e:
            print("[SLOTS] Error manejando mensaje:", e)
