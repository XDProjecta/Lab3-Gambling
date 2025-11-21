# client/scenes/blackjack_scene.py
"""
BlackjackScene
--------------
Interfaz del juego de Blackjack para el cliente.

FUNCIONES:
- Unirse a la mesa (MSG_BJ_JOIN)
- Iniciar ronda (solo host → MSG_BJ_START)
- Recibir cartas (MSG_BJ_DEAL)
- Enviar acciones HIT / STAND (MSG_BJ_ACTION)
- Mostrar mensajes del servidor
- Mostrar resultado final (MSG_BJ_RESULT)

La lógica del juego NO está aquí → está en server/games/blackjack.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from common.messages import *
from client.widgets.card_drawer import card_to_text
from client.widgets.sprites import draw_card

BG = "#081018"
CARD_BG = "#fffdf2"
TXT = "#f3f3f3"


class BlackjackScene(tk.Frame):
    def __init__(self, parent, app):
        """
        parent : contenedor principal
        app    : referencia para net, client_id y cambio de escena

        Atributos:
        - hand: lista de cartas del jugador
        - dealer_show: carta visible del dealer
        """
        super().__init__(parent, bg=BG)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id

        self.hand = []
        self.dealer_show = None

        self.build()

    def build(self):
        """Dibuja toda la interfaz visual del blackjack."""
        self.pack(fill="both", expand=True)

        header = tk.Label(self, text="BLACKJACK - MESA",
                          font=("Arial", 18), bg=BG, fg="#ffd27a")
        header.pack(pady=8)

        # Canvas donde se dibujan cartas
        self.table = tk.Canvas(self, width=760, height=240,
                               bg="#0b1a1c", highlightthickness=0)
        self.table.pack(padx=8, pady=8)

        # Textos guía
        self.table.create_text(380, 20, text="Dealer", fill="#ff9a2e")
        self.table.create_text(380, 120, text="TUS CARTAS", fill="#2ef0f0")

        # Controles
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=6)

        tk.Button(ctrl, text="Unirse a mesa",
                  command=self.join_table, bg="#ffd27a").pack(side="left", padx=6)

        tk.Button(ctrl, text="Iniciar ronda (host)",
                  command=self.start_round, bg="#ff7ab6").pack(side="left", padx=6)

        self.hit_btn = tk.Button(ctrl, text="HIT",
                                 state="disabled",
                                 command=lambda: self.send_action("HIT"),
                                 bg="#8affa1")
        self.hit_btn.pack(side="left", padx=6)

        self.stand_btn = tk.Button(ctrl, text="STAND",
                                   state="disabled",
                                   command=lambda: self.send_action("STAND"),
                                   bg="#ff9a2e")
        self.stand_btn.pack(side="left", padx=6)

        tk.Button(ctrl, text="Volver",
                  command=lambda: self.app.show_scene("MENU")).pack(side="left", padx=6)

        # Log inferior
        self.log = tk.Text(self, height=6, bg="#071219", fg=TXT)
        self.log.pack(fill="x", padx=8, pady=8)

    def log_msg(self, s):
        """Escribe una línea en el log informativo."""
        self.log.insert("end", s + "\n")
        self.log.see("end")

    # ---------------------------------------------------------
    # ACCIONES DEL CLIENTE → SERVIDOR
    # ---------------------------------------------------------

    def join_table(self):
        """Envía solicitud para unirse a una mesa de blackjack."""
        if self.net and getattr(self.net, "connected", False):
            self.net.send({"type": MSG_BJ_JOIN, "client_id": self.client_id})
            self.log_msg("Solicitado unirse a mesa.")

    def start_round(self):
        """Solo el host debería usarlo. Pide iniciar la ronda."""
        if self.net and getattr(self.net, "connected", False):
            self.net.send({"type": MSG_BJ_START, "client_id": self.client_id})
            self.log_msg("Solicitado iniciar ronda.")

    def send_action(self, action):
        """Envía HIT o STAND al servidor."""
        # si estamos conectados al servidor, entonces enviamos el mensaje al servidor en formato diccionario
        if self.net and getattr(self.net, "connected", False):
            self.net.send({
                "type": MSG_BJ_ACTION,
                "client_id": self.client_id,
                "action": action
            })
            # registramos en el log la acción enviada
            self.log_msg(f"Enviado: {action}")

            # Se deshabilitan hasta recibir "REQUEST" de nuevo para evitar múltiples envíos rápidos
            self.hit_btn.config(state="disabled")
            self.stand_btn.config(state="disabled")

    # ---------------------------------------------------------
    # MANEJO DE MENSAJES DEL SERVIDOR
    # ---------------------------------------------------------

    def handle_server_msg(self, msg):
        """
        Maneja mensajes específicos para blackjack.
        Tipos esperados:
        - MSG_BJ_DEAL
        - MSG_BJ_UPDATE
        - MSG_BJ_RESULT
        """
        typ = msg.get("type")

        if typ == MSG_BJ_DEAL:
            to = msg.get("to")

            # Si la carta es para este cliente
            if to == self.client_id:
                hand = msg.get("hand")

                # Hand puede ser lista completa o una sola carta en lista
                if isinstance(hand, list):
                    self.hand = hand
                else:
                    self.hand.append(hand)

                self._draw_hand()

            # Actualizar carta visible del dealer
            dealer_show = msg.get("dealer_show")
            if dealer_show:
                self.dealer_show = dealer_show
                self._draw_dealer_show()

            self.log_msg("Carta(s) recibida(s).")

        elif typ == MSG_BJ_UPDATE:
            txt = msg.get("msg", "")
            self.log_msg(txt)

            if msg.get("action") == "REQUEST":
                self.hit_btn.config(state="normal")
                self.stand_btn.config(state="normal")

        elif typ == MSG_BJ_RESULT:
            res = msg.get("result")
            dealer_hand = msg.get("dealer_hand")

            self.log_msg(f"Resultado: {res}")
            messagebox.showinfo("Resultado", str(res))

    # ---------------------------------------------------------
    # DIBUJADO DE CARTAS
    # ---------------------------------------------------------

    def _draw_hand(self):
        """Dibuja en pantalla las cartas actuales del jugador."""
        self.table.delete("player_card")

        x0, y0 = 220, 150
        offset = 90

        for i, c in enumerate(self.hand):
            rank, suit = c
            draw_card(self.table, x0 + i * offset, y0,
                      w=70, h=100,
                      rank=rank, suit=suit,
                      fill="#fffdf2")

        # etiqueta para poder borrar fácil
        self.table.addtag_withtag("player_card", "all")

    def _draw_dealer_show(self):
        """
        Dibuja la carta visible del dealer (solo la primera).
        """
        self.table.delete("dealer_card")

        if not self.dealer_show:
            return

        rank, suit = self.dealer_show

        draw_card(self.table, 360, 40,
                  w=70, h=100,
                  rank=rank, suit=suit,
                  fill="#fff")

        self.table.addtag_withtag("dealer_card", "all")
