# client/scenes/blackjack_scene.py
import tkinter as tk
from tkinter import ttk, messagebox
from common.messages import *
from client.widgets.card_drawer import card_to_text

class BlackjackScene(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id
        self.hand = []
        self.dealer_show = None
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)
        ttk.Label(self, text="Blackjack - Mesa Multijugador", font=("Arial", 18)).pack(pady=8)
        frame = ttk.Frame(self)
        frame.pack(pady=6)
        ttk.Label(frame, text="Tus cartas:").grid(row=0, column=0, sticky="w")
        self.cards_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.cards_var, font=("Arial", 14)).grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text="Carta dealer (visible):").grid(row=2, column=0, sticky="w")
        self.dealer_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.dealer_var, font=("Arial", 14)).grid(row=3, column=0, sticky="w")

        btns = ttk.Frame(self)
        btns.pack(pady=8)
        ttk.Button(btns, text="Unirse a mesa", command=self.join_table).pack(side="left", padx=4)
        ttk.Button(btns, text="Iniciar ronda (host)", command=self.start_round).pack(side="left", padx=4)
        self.hit_btn = ttk.Button(btns, text="HIT", command=lambda: self.send_action("HIT"), state="disabled")
        self.hit_btn.pack(side="left", padx=4)
        self.stand_btn = ttk.Button(btns, text="STAND", command=lambda: self.send_action("STAND"), state="disabled")
        self.stand_btn.pack(side="left", padx=4)

        self.log = tk.Text(self, height=8)
        self.log.pack(fill="both", padx=8, pady=8)

    def log_msg(self, s):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def join_table(self):
        if self.net and self.net.connected:
            self.net.send({"type": MSG_BJ_JOIN, "client_id": self.client_id})
            self.log_msg("Solicitado unirse a mesa.")

    def start_round(self):
        if self.net and self.net.connected:
            self.net.send({"type": MSG_BJ_START, "client_id": self.client_id})
            self.log_msg("Solicitado iniciar ronda.")

    def send_action(self, action):
        if self.net and self.net.connected:
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
                # hand puede ser lista (initial) o lista con una carta
                if isinstance(hand, list):
                    self.hand = hand
                else:
                    self.hand.append(hand)
                self.cards_var.set(" ".join(card_to_text(c) for c in self.hand))
            dealer_show = msg.get("dealer_show")
            if dealer_show:
                self.dealer_var.set(card_to_text(tuple(dealer_show)))
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
            self.log_msg(f"Resultado: {res}  Dealer: {' '.join(card_to_text(tuple(x)) for x in dealer_hand)}")
            messagebox.showinfo("Resultado", str(res))
