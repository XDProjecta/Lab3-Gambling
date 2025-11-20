import tkinter as tk
from tkinter import ttk
import random

class MenuScene(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)

        # Fondo oscuro tipo casino
        self.config(style="Dark.TFrame")

        # Título neón animado
        title = ttk.Label(self, text="★ CASINO ★", style="Neon.TLabel")
        title.pack(pady=30)

        # Marco central
        frame = ttk.Frame(self, style="Dark.TFrame")
        frame.pack(pady=15)

        # Botones con efecto hover
        self._make_button(frame, "🐀 Carrera de Ratones", lambda: self.app.show_scene("RACE")).pack(pady=10)
        self._make_button(frame, "🂡 Blackjack", lambda: self.app.show_scene("BLACKJACK")).pack(pady=10)
        self._make_button(frame, "🎰 Slots", lambda: self.app.show_scene("SLOTS")).pack(pady=10)

        # Decoración inferior
        deco = ttk.Label(self, text="──────── ✦ ✦ ✦ ────────", style="Deco.TLabel")
        deco.pack(pady=20)

    def _make_button(self, parent, text, cmd):
        btn = ttk.Button(parent, text=text, command=cmd, style="Menu.TButton")

        # efecto hover
        def on_enter(e):
            btn.config(style="MenuHover.TButton")

        def on_leave(e):
            btn.config(style="Menu.TButton")

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn


# Estilos retro
def setup_menu_styles(root):
    style = ttk.Style(root)

    style.configure(
        "Dark.TFrame",
        background="#0b0f1a"  # azul oscuro tipo casino
    )

    style.configure(
        "Neon.TLabel",
        font=("Arial Black", 32),
        foreground="#ff006a",      # rosa neón
        background="#0b0f1a"
    )

    style.configure(
        "Deco.TLabel",
        font=("Consolas", 14),
        foreground="#ffdd55",
        background="#0b0f1a"
    )

    style.configure(
        "Menu.TButton",
        font=("Arial", 18, "bold"),
        padding=12,
        foreground="white",
        background="#1b2236",
        borderwidth=0
    )

    style.map(
        "Menu.TButton",
        background=[("active", "#232d4a")]
    )

    style.configure(
        "MenuHover.TButton",
        font=("Arial", 18, "bold"),
        padding=12,
        foreground="#ffdd55",
        background="#2c3557",
        borderwidth=0
    )
