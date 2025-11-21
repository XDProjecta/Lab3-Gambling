# gui_client.py
"""
GUI Client
----------
Este archivo controla toda la aplicación gráfica del CLIENTE.

FUNCIONES PRINCIPALES:
- Conectarse al servidor (TCP)
- Mantener un hilo escuchando mensajes del servidor
- Redireccionar mensajes a las escenas correspondientes
- Administrar navegación entre escenas (Menu, Race, Blackjack, Slots)

IMPORTANTE:
Las escenas NO manejan directamente los sockets.
Todo mensaje entrante pasa por gui_client.py.
"""

import tkinter as tk
from tkinter import ttk
import threading
import json
import socket
from common.messages import *
from config.config import CONFIG_PARAMS

# Escenas
from client.scenes.menu_scene import MenuScene
from client.scenes.rat_race_scene import RaceScene
from client.scenes.slots_scene import SlotsScene
from client.scenes.blackjack_scene import BlackjackScene


class NetworkClient:
    """
    Esta clase maneja TODA la comunicación de red del cliente.

    MÉTODOS:
    - connect(): se conecta al servidor TCP
    - send(data): envía un dict convertido en JSON
    - listen(): escucha en segundo plano todos los mensajes
    """

    def __init__(self, host, port, on_message):
        self.host = host
        self.port = port
        self.socket = None
        self.on_message = on_message  # callback hacia gui_client
        self.connected = False

    def connect(self):
        """Intenta conectarse al servidor."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True

            # Iniciar hilo que escucha mensajes del server
            threading.Thread(target=self.listen, daemon=True).start()
            print("[CLIENT] Conectado al servidor.")
        except Exception as e:
            print("[CLIENT] Error conectando:", e)
            self.connected = False

    def listen(self):
        """
        Hilo en segundo plano:
        lee línea por línea y las envía a gui_client.on_message().
        """
        try:
            while self.connected:
                data = self.socket.recv(4096)
                if not data:
                    print("[CLIENT] Servidor cerró conexión.")
                    self.connected = False
                    break

                for line in data.split(b"\n"):
                    if not line.strip():
                        continue

                    try:
                        msg = json.loads(line.decode())
                        self.on_message(msg)
                    except Exception as e:
                        print("[CLIENT] Error procesando JSON:", e)

        except Exception as e:
            print("[CLIENT] Error en listen():", e)
        finally:
            self.connected = False
            self.socket.close()

    def send(self, data):
        """Convierte el dict en JSON y lo manda al servidor."""
        try:
            if self.connected:
                raw = json.dumps(data).encode() + b"\n"
                self.socket.sendall(raw)
        except Exception as e:
            print("[CLIENT] Error enviando:", e)


# ------------------------------------------------------------
#               APLICACIÓN PRINCIPAL DEL CLIENTE
# ------------------------------------------------------------

class ClientApp:
    """
    Maneja:
    - Las escenas
    - El cliente TCP
    - El enrutado de mensajes entrantes
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Casino - Cliente")
        self.root.geometry("900x500")

        # ID del cliente (asignado por el server)
        self.client_id = None

        # Crear contenedor donde van todas las escenas
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Iniciar red
        host = CONFIG_PARAMS["SERVER_HOST"]
        port = CONFIG_PARAMS["SERVER_PORT"]

        self.net = NetworkClient(host, port, self.on_message)
        self.net.connect()

        # Inicializar escenas
        self.scenes = {}
        self.current_scene = None

        self.init_scenes()
        self.show_scene("MENU")

    def init_scenes(self):
        """Crea e instancia todas las escenas del cliente."""

        self.scenes["MENU"] = MenuScene(self.main_frame, self)
        self.scenes["RACE"] = RaceScene(self.main_frame, self)
        self.scenes["SLOTS"] = SlotsScene(self.main_frame, self)
        self.scenes["BLACKJACK"] = BlackjackScene(self.main_frame, self)

    def show_scene(self, name):
        """Cambia la escena visible."""
        if self.current_scene:
            self.scenes[self.current_scene].pack_forget()

        self.current_scene = name
        self.scenes[name].pack(fill="both", expand=True)

    # ------------------------------------------------------------
    #            RECEPCIÓN DE MENSAJES DEL SERVIDOR
    # ------------------------------------------------------------

    def on_message(self, msg):
        """
        Punto central donde el CLIENTE recibe TODO mensaje del servidor.
        Aquí se enrutan hacia la escena correspondiente.
        """

        # Si el servidor nos asigna un ID
        if msg.get("type") == MSG_REGISTER:
            self.client_id = msg["client_id"]
            print(f"[CLIENT] Registrado como: {self.client_id}")
            return

        # Rat Race - GAME STATE → debe ir a la escena
        if msg.get("type") == "GAME_STATE":
            scene = self.scenes["RACE"]
            for m, pos in msg["positions"].items():
                if m in scene.canvas_objects:
                    obj = scene.canvas_objects[m]
                    y = scene.canvas.coords(obj)[1]
                    scene.local_pos[m] = pos
                    scene.canvas.coords(obj, 20 + pos, y)
            return

        # Cualquier mensaje específico de escenas:
        scene = self.scenes.get("RACE")
        if scene:
            scene.handle_server_msg(msg)

        scene = self.scenes.get("SLOTS")
        if scene:
            scene.handle_server_msg(msg)

        scene = self.scenes.get("BLACKJACK")
        if scene:
            scene.handle_server_msg(msg)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ClientApp()
    app.run()
