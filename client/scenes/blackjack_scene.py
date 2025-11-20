# client/scenes/blackjack_scene.py
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
        super().__init__(parent, bg=BG)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id
        self.hand = []
        self.dealer_show = None
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)
        header = tk.Label(self, text="BLACKJACK - MESA", font=("Arial", 18), bg=BG, fg="#ffd27a")
        header.pack(pady=8)

        self.table = tk.Canvas(self, width=760, height=240, bg="#0b1a1c", highlightthickness=0)
        self.table.pack(padx=8, pady=8)

        # áreas: dealer y player
        self.table.create_text(380, 20, text="Dealer", fill="#ff9a2e")
        self.table.create_text(380, 120, text="TUS CARTAS", fill="#2ef0f0")

        # controles
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=6)
        tk.Button(ctrl, text="Unirse a mesa", command=self.join_table, bg="#ffd27a").pack(side="left", padx=6)
        tk.Button(ctrl, text="Iniciar ronda (host)", command=self.start_round, bg="#ff7ab6").pack(side="left", padx=6)
        self.hit_btn = tk.Button(ctrl, text="HIT", command=lambda: self.send_action("HIT"), state="disabled", bg="#8affa1")
        self.hit_btn.pack(side="left", padx=6)
        self.stand_btn = tk.Button(ctrl, text="STAND", command=lambda: self.send_action("STAND"), state="disabled", bg="#ff9a2e")
        self.stand_btn.pack(side="left", padx=6)
        tk.Button(ctrl, text="Volver", command=lambda: self.app.show_scene("MENU")).pack(side="left", padx=6)

        # log
        self.log = tk.Text(self, height=6, bg="#071219", fg=TXT)
        self.log.pack(fill="x", padx=8, pady=8)

    def log_msg(self, s):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def join_table(self):
        if self.net and getattr(self.net, "connected", False):
            self.net.send({"type": MSG_BJ_JOIN, "client_id": self.client_id})
            self.log_msg("Solicitado unirse a mesa.")

    def start_round(self):
        if self.net and getattr(self.net, "connected", False):
            self.net.send({"type": MSG_BJ_START, "client_id": self.client_id})
            self.log_msg("Solicitado iniciar ronda.")

    def send_action(self, action):
        if self.net and getattr(self.net, "connected", False):
            self.net.send({"type": MSG_BJ_ACTION, "client_id": self.client_id, "action": action})
            self.log_msg(f"Enviado: {action}")
            self.hit_btn.config(state="disabled")
            self.stand_btn.config(state="disabled")

    def handle_server_msg(self, msg):
        typ = msg.get("type")
        if typ == MSG_BJ_DEAL:
            to = msg.get("to")
            if to == self.client_id:
                hand = msg.get("hand")
                if isinstance(hand, list):
                    self.hand = hand
                else:
                    self.hand.append(hand)
                self._draw_hand()
            dealer_show = msg.get("dealer_show")
            if dealer_show:
                self.dealer_show = dealer_show
                self._draw_dealer_show()
            self.log_msg("Carta(s) recibida(s).")
        elif typ == MSG_BJ_UPDATE:
            txt = msg.get("msg","")
            self.log_msg(txt)
            if msg.get("action") == "REQUEST":
                self.hit_btn.config(state="normal")
                self.stand_btn.config(state="normal")
        elif typ == MSG_BJ_RESULT:
            res = msg.get("result")
            dealer_hand = msg.get("dealer_hand")
            self.log_msg(f"Resultado: {res}")
            messagebox.showinfo("Resultado", str(res))

    def _draw_hand(self):
        # limpia área inferior y dibuja cartas del jugador
        self.table.delete("player_card")
        x0 = 220
        y0 = 150
        offset = 90
        for i, c in enumerate(self.hand):
            # c puede ser lista/tupla ["A","♠"] o ["10","♥"]
            rank, suit = c
            draw_card(self.table, x0 + i*offset, y0, w=70, h=100, rank=rank, suit=suit, fill="#fffdf2")
            # tag para borrado
            self.table.addtag_withtag("player_card", "all")
        # nota: draw_card devuelve rect, para tags usamos "player_card" simplificado

    def _draw_dealer_show(self):
        self.table.delete("dealer_card")
        if not self.dealer_show:
            return
        # dealer card visible (centro arriba)
        rank, suit = self.dealer_show
        draw_card(self.table, 360, 40, w=70, h=100, rank=rank, suit=suit, fill="#fff")
        self.table.addtag_withtag("dealer_card", "all")
