# client/scenes/menu_scene.py
"""
MenuScene
---------
Esta escena representa el menú principal del cliente.
Aquí el jugador puede escoger entre los juegos:
- Carrera de Ratones
- Blackjack
- Slots

La escena no maneja lógica de red.  
Solo usa self.app.show_scene("...") para navegar.
"""

import tkinter as tk
from tkinter import ttk
import random

class MenuScene(ttk.Frame):
    def __init__(self, parent, app):
        """
        parent : Frame contenedor dentro del panel principal del cliente
        app    : referencia al ClientApp → permite cambiar de escena

        Esta clase solo construye botones y estilos visuales.
        """
        super().__init__(parent)
        self.app = app
        self.build()

    def build(self):
        """Construye todo el layout visual del menú."""
        self.pack(fill="both", expand=True)

        # Fondo general del menú (color oscuro tipo casino)
        self.config(style="Dark.TFrame")

        # Texto del título con estilo neón
        title = ttk.Label(self, text="★ CASINO ★", style="Neon.TLabel")
        title.pack(pady=30)

        # Marco donde viven los botones principales
        frame = ttk.Frame(self, style="Dark.TFrame")
        frame.pack(pady=15)

        # Botones del menú → cambian entre escenas
        self._make_button(frame, "🐀 Carrera de Ratones",
                          lambda: self.app.show_scene("RACE")).pack(pady=10)

        self._make_button(frame, "🂡 Blackjack",
                          lambda: self.app.show_scene("BLACKJACK")).pack(pady=10)

        self._make_button(frame, "🎰 Slots",
                          lambda: self.app.show_scene("SLOTS")).pack(pady=10)

        # Línea decorativa inferior
        deco = ttk.Label(self, text="──────── ✦ ✦ ✦ ────────",
                         style="Deco.TLabel")
        deco.pack(pady=20)

    def _make_button(self, parent, text, cmd):
        """
        Crea un botón personalizado con efecto ‘hover’.
        Este método evita repetir código.
        """
        btn = ttk.Button(parent, text=text, command=cmd,
                         style="Menu.TButton")

        # Efecto hover al pasar el mouse
        def on_enter(e):
            btn.config(style="MenuHover.TButton")

        def on_leave(e):
            btn.config(style="Menu.TButton")

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn


# --------------------------------------------------------
# Estilos gráficos propios del menú principal
# --------------------------------------------------------

def setup_menu_styles(root):
    """
    Define los estilos visuales usados en el menú:
    colores, fuentes, aspecto de los botones, etc.
    """

    style = ttk.Style(root)

    style.configure("Dark.TFrame", background="#0b0f1a")

    style.configure("Neon.TLabel",
                    font=("Arial Black", 32),
                    foreground="#ff006a",
                    background="#0b0f1a")

    style.configure("Deco.TLabel",
                    font=("Consolas", 14),
                    foreground="#ffdd55",
                    background="#0b0f1a")

    # Estilo por defecto del botón
    style.configure("Menu.TButton",
                    font=("Arial", 18, "bold"),
                    padding=12,
                    foreground="white",
                    background="#1b2236",
                    borderwidth=0)

    style.map("Menu.TButton",
              background=[("active", "#232d4a")])

    # Estilo cuando el mouse pasa por encima
    style.configure("MenuHover.TButton",
                    font=("Arial", 18, "bold"),
                    padding=12,
                    foreground="#ffdd55",
                    background="#2c3557",
                    borderwidth=0)
