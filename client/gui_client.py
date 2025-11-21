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
pues todo pasa por aquí (ClientApp).
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
        self.on_message = on_message  # callback hacia gui_client para mensajes entrantes
        self.connected = False

    def connect(self):
        """Intenta conectarse al servidor."""
        try:
            # si no hay conexión, crear socket y conectarse
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # conectarse al servidor por host y puerto
            self.socket.connect((self.host, self.port))
            # marcar como conectado
            self.connected = True

            # Iniciar hilo que escucha mensajes del server, daemon para que cierre con la app
            #  para así evitar bloqueos cuando se cierra la GUI del cliente
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
                # si no hay datos, el servidor cerró la conexión
                data = self.socket.recv(4096)
                if not data:
                    print("[CLIENT] Servidor cerró conexión.")
                    self.connected = False
                    break
                # procesar cada línea recibida como un mensaje JSON
                for line in data.split(b"\n"):
                    if not line.strip():
                        continue

                    try:
                        # decodificar JSON y llamar al callback
                        msg = json.loads(line.decode())
                        # llamar al callback con el mensaje recibido por medio de on_message
                        self.on_message(msg)
                    except Exception as e:
                        print("[CLIENT] Error procesando JSON:", e)

        except Exception as e:
            print("[CLIENT] Error en listen():", e)
        finally:
            # cerrar conexión en caso de error
            self.connected = False
            self.socket.close()

    def send(self, data):
        """Convierte el dict en JSON y lo manda al servidor."""
        # si no estamos conectados, no hacemos nada
        # si estamos conectados, enviamos el mensaje
        try:
            if self.connected:
                # raw es el mensaje en bytes listo para enviar
                # se agrega \n para que el servidor pueda separar mensajes
                # sendall asegura que se envíen todos los bytes del mensaje
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

        # Inicializar escenas y navegación por medio de show_scene() y current_scene
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
            # si hay una escena activa, ocultarla
            self.scenes[self.current_scene].pack_forget()
        # si la escena existe, mostrarla
        self.current_scene = name
        self.scenes[name].pack(fill="both", expand=True)

    # ------------------------------------------------------------
    #            RECEPCIÓN DE MENSAJES DEL SERVIDOR
    # ------------------------------------------------------------

    def on_message(self, msg):
        """
        Punto central donde el CLIENTE recibe TODOO mensaje del servidor.
        Aquí se enrutan hacia la escena correspondiente.
        """

        # Si el servidor nos asigna un ID
        if msg.get("type") == MSG_REGISTER:
            # guardar el client_id asignado por el servidor por medio del mensaje REGISTER
            self.client_id = msg["client_id"]
            print(f"[CLIENT] Registrado como: {self.client_id}")
            return

        # Rat Race - GAME STATE → debe ir a la escena
        # si el mensaje es de tipo GAME_STATE, y hay una escena de RACE, es decir, si está mostrándose rat race, 
        # entonces actualizamos las posiciones de los ratones en la escena de carrera
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
        # si la escena es de RACE, entonces llamamos a su método handle_server_msg con el mensaje recibido
        if scene:
            scene.handle_server_msg(msg)
        # si la escena es de SLOTS, entonces llamamos a su método handle_server_msg con el mensaje recibido
        scene = self.scenes.get("SLOTS")
        if scene:
            scene.handle_server_msg(msg)
        # si la escena es de BLACKJACK, entonces llamamos a su método handle_server_msg con el mensaje recibido
        scene = self.scenes.get("BLACKJACK")
        if scene:
            scene.handle_server_msg(msg)

    # esta función inicia el loop principal de la GUI para que se muestre la ventana
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ClientApp()
    app.run()
