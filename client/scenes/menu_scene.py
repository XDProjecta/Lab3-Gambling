# client/scenes/menu_scene.py
import tkinter as tk
from tkinter import ttk

class MenuScene(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)
        ttk.Label(self, text="CASINO - MENÚ", font=("Arial", 24)).pack(pady=20)
        btns = ttk.Frame(self)
        btns.pack(pady=8)
        ttk.Button(btns, text="Carrera de Ratones", width=28, command=lambda: self.app.show_scene("RACE")).pack(pady=6)
        ttk.Button(btns, text="BlackJack (Multijugador)", width=28, command=lambda: self.app.show_scene("BLACKJACK")).pack(pady=6)
        ttk.Button(btns, text="Slots (Tragamonedas)", width=28, command=lambda: self.app.show_scene("SLOTS")).pack(pady=6)
