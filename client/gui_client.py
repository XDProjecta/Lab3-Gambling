# client/gui_client.py
"""
GUI principal casino jijij para el cliente.
Maneja escena, conexión de red y estilo general.
"""
import tkinter as tk
from tkinter import ttk
import uuid
from client.client import NetworkClient
from client.scenes.menu_scene import MenuScene
from client.scenes.rat_race_scene import RaceScene
from client.scenes.blackjack_scene import BlackjackScene
from client.scenes.slots_scene import SlotsScene
from config.config import CONFIG_PARAMS

# Paleta retro
BG = "#0b0710"        # fondo oscuro
PANEL = "#101420"     # paneles más claros
NEON_PINK = "#ff48a6"
NEON_CYAN = "#2ef0f0"
NEON_ORANGE = "#ff9a2e"
TEXT = "#f3f3f3"

class ClientApp:
    def __init__(self, root, client_id=None):
        self.root = root
        self.client_id = client_id or f"player-{str(uuid.uuid4())[:6]}"
        # objeto de red (ver client/client.py)
        self.net = NetworkClient(self.client_id, on_message=self.on_message)
        self.scenes = {}
        self.current_scene = None
        self._build_ui()
        # intenta conectar (si falla, GUI sigue funcionando)
        try:
            self.net.connect()
        except Exception as e:
            print("[CLIENT] No se pudo conectar automáticamente:", e)

    def _build_ui(self):
        # estilo global
        self.root.title("CASINO — Cliente")
        self.root.configure(bg=BG)
        # contenedor principal
        container = tk.Frame(self.root, bg=BG, padx=10, pady=10)
        container.pack(fill="both", expand=True)

        # top bar - logo neón
        top = tk.Frame(container, bg=BG)
        top.pack(fill="x", pady=(0,8))
        # canvas para logo neon
        logo = tk.Canvas(top, height=70, bg=BG, highlightthickness=0)
        logo.pack(side="left", padx=(10,20))
        self._draw_neon_logo(logo)

        # status
        self.status_var = tk.StringVar(value="Conexión: desconectado")
        status_lbl = tk.Label(top, textvariable=self.status_var, bg=BG, fg=NEON_CYAN, font=("Arial", 10, "bold"))
        status_lbl.pack(side="right", padx=10)

        # panel principal (escenas)
        panel = tk.Frame(container, bg=PANEL, bd=0)
        panel.pack(fill="both", expand=True)
        panel.pack_propagate(False)
        panel.config(width=900, height=600)

        # crear escenas y pasar referencia
        self.scenes["MENU"] = MenuScene(panel, self)
        self.scenes["RACE"] = RaceScene(panel, self)
        self.scenes["BLACKJACK"] = BlackjackScene(panel, self)
        self.scenes["SLOTS"] = SlotsScene(panel, self)

        # mostrar menu inicial
        self.show_scene("MENU")

        # actualizador simple de estado
        self.root.after(1000, self._update_status)

    def _draw_neon_logo(self, c: tk.Canvas):
        # logo estilo retro: do you known what time it is???
        w = 420; h = 70
        c.config(width=w, height=h)
        # rectángulo exterior glow
        for i, col in enumerate([NEON_CYAN, NEON_PINK, NEON_ORANGE]):
            c.create_rectangle(6-i,6-i,w-6+i,h-6+i, outline=col, width=2, stipple="")
        # texto
        c.create_text(w//2, h//2, text="CASINO RETRO", font=("Press Start 2P", 18), fill=NEON_PINK)

    def show_scene(self, key):
        # ocultar todas y mostrar la solicitada
        for s in self.scenes.values():
            try:
                s.pack_forget()
            except:
                pass
        scene = self.scenes.get(key)
        if scene:
            scene.pack(fill="both", expand=True)
            self.current_scene = scene

    def on_message(self, msg):
        # distribuir mensajes a la escena actual si implementa handler
        typ = msg.get("type")
        if typ == "REGISTERED":
            self.status_var.set(f"Conexión: registrado ({msg.get('client_id')})")
            print("[CLIENT] Registrado en servidor:", msg.get("client_id"))
            return
        # si la escena tiene handler lo ejecutamos (por ejemplo Blackjack/Slots)
        if self.current_scene and hasattr(self.current_scene, "handle_server_msg"):
            try:
                self.current_scene.handle_server_msg(msg)
            except Exception as e:
                print("[CLIENT] Error manejando mensaje en escena:", e)

    def _update_status(self):
        # actualiza indicador de conexión
        st = "conectado" if (self.net and getattr(self.net, "connected", False)) else "desconectado"
        self.status_var.set(f"Conexión: {st} — {self.client_id}")
        self.root.after(1000, self._update_status)

