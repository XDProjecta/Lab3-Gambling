# server/server.py
"""
Servidor TCP principal.
- Acepta clientes
- Mantiene lista de clientes conectados
- Recibe mensajes y los delega al GameManager
- Envía respuestas o broadcast
"""

import socket
import threading
from config.config import CONFIG_PARAMS
from common.protocol import make_msg, parse_stream
from server.game_manager import GameManager

# Carga de direcciones desde config.json
HOST = CONFIG_PARAMS["SERVER_IP_ADDRESS"]
PORT = CONFIG_PARAMS["SERVER_PORT"]

class Server:
    def __init__(self, host=HOST, port=PORT):
        """
        Constructor del servidor.
        - Inicializa socket TCP
        - Estructuras para manejar clientes
        - Crea instancia del GameManager que coordina los juegos
        """
        self.host = host
        self.port = port

        # Socket TCP del servidor
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Diccionario de clientes conectados:
        # { socket : client_id }
        self.clients = {}
        self.clients_lock = threading.Lock()

        self.running = False

        # GameManager controla rat race, blackjack, slots, etc.
        self.manager = GameManager(self)

    def start(self):
        """
        Inicia el servidor TCP:
        - Bindea IP/PORT
        - Comienza a escuchar conexiones entrantes
        - Lanza hilo que acepta clientes
        """
        self.sock.bind((self.host, self.port))
        self.sock.listen(CONFIG_PARAMS["SERVER_MAX_CLIENTS"])
        self.running = True

        print(f"[SERVER] Escuchando en {self.host}:{self.port}")

        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        """
        Hilo principal que acepta nuevos clientes.
        Cada cliente se atiende en un hilo separado.
        """
        while self.running:
            try:
                csock, addr = self.sock.accept()
                print("[SERVER] Nueva conexión desde", addr)

                # Crear hilo exclusivo para leer mensajes del cliente
                threading.Thread(target=self._handle_client, args=(csock,), daemon=True).start()

            except Exception as e:
                print("[SERVER] Error en accept:", e)

    def _handle_client(self, csock):
        """
        Maneja un cliente:
        - Lee mensajes continuamente
        - Parsea mensajes según nuestro protocolo
        - Si es REGISTER → registra el cliente
        - Si no → delega al GameManager
        """
        addr = None
        client_id = None
        buf = b""  # buffer para fragmentación TCP

        try:
            addr = csock.getpeername()

            while True:
                data = csock.recv(4096)
                if not data:
                    break  # cliente desconectado

                buf += data

                # parse_stream devuelve una lista de mensajes completos
                msgs = parse_stream(buf)
                buf = b""  # limpiar buffer

                for msg in msgs:
                    print(f"[SERVER] Mensaje recibido de {addr}: {msg}")

                    # Registro inicial
                    if msg.get("type") == "REGISTER":
                        client_id = msg.get("client_id")

                        # Guardamos el cliente en el diccionario
                        with self.clients_lock:
                            self.clients[csock] = client_id

                        # Respuesta confirmando registro
                        csock.sendall(make_msg({
                            "type":"REGISTERED",
                            "client_id": client_id
                        }))

                        # Notificamos al GameManager
                        self.manager.on_client_register(client_id, csock)
                        continue

                    # Cualquier otro mensaje va al GameManager
                    self.manager.process_message(msg, csock)

        except Exception as e:
            print(f"[SERVER] Error manejando cliente {addr}: {e}")

        finally:
            print(f"[SERVER] Cliente desconectado {addr}")

            # Sacamos al cliente del dict
            with self.clients_lock:
                self.clients.pop(csock, None)

            # Notificar al GameManager
            try:
                self.manager.on_client_disconnect(client_id, csock)
            except:
                pass

            # Cerrar socket del cliente
            try:
                csock.close()
            except:
                pass

    def send(self, csock, obj):
        """
        Envia un mensaje a un cliente.
        """
        try:
            csock.sendall(make_msg(obj))
        except:
            pass  # Si falla, se maneja en otro lado

    def broadcast(self, obj):
        """
        Envía un mensaje a TODOS los clientes conectados.
        """
        with self.clients_lock:
            for csock in list(self.clients.keys()):
                try:
                    csock.sendall(make_msg(obj))
                except:
                    pass  # se limpiará en el hilo del cliente

    def stop(self):
        """
        Apaga el servidor completamente.
        """
        self.running = False

        try:
            self.sock.close()
        except:
            pass

        # Cerrar clientes
        with self.clients_lock:
            for csock in list(self.clients.keys()):
                try:
                    csock.close()
                except:
                    pass

        print("[SERVER] Servidor detenido.")
