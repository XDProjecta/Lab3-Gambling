# client/gui_client.py
"""
GUI principal del cliente: maneja escenas y la conexión de red.
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

class ClientApp:
    def __init__(self, root, client_id=None):
        self.root = root
        self.client_id = client_id or f"client-{str(uuid.uuid4())[:6]}"
        self.net = NetworkClient(self.client_id, on_message=self.on_message)
        self.scenes = {}
        self.current_scene = None
        self._build_ui()
        # intenta conectar con los valores en config
        try:
            self.net.connect()
        except Exception as e:
            print("No se pudo conectar automáticamente:", e)

    def _build_ui(self):
        self.root.title("Cliente - ProyectoCasino")
        container = ttk.Frame(self.root, padding=8)
        container.pack(fill="both", expand=True)
        # crear escenas
        self.scenes["MENU"] = MenuScene(container, self)
        self.scenes["RACE"] = RaceScene(container, self)
        self.scenes["BLACKJACK"] = BlackjackScene(container, self)
        self.scenes["SLOTS"] = SlotsScene(container, self)
        self.show_scene("MENU")

    def show_scene(self, key):
        # esconder todas
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
            print("Registrado en servidor:", msg.get("client_id"))
            return
        if self.current_scene and hasattr(self.current_scene, "handle_server_msg"):
            try:
                self.current_scene.handle_server_msg(msg)
            except Exception as e:
                print("Error manejando mensaje en escena:", e)
