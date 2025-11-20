# server/server.py
"""
Servidor TCP principal.
Acepta clientes y delega mensajes al GameManager.
"""
import socket
import threading
from config.config import CONFIG_PARAMS
from common.protocol import make_msg, parse_stream
from server.game_manager import GameManager

HOST = CONFIG_PARAMS["SERVER_IP_ADDRESS"]
PORT = CONFIG_PARAMS["SERVER_PORT"]

class Server:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # socket -> client_id
        self.clients_lock = threading.Lock()
        self.running = False
        self.manager = GameManager(self)

    def start(self):
        # bind y listen
        self.sock.bind((self.host, self.port))
        self.sock.listen(CONFIG_PARAMS["SERVER_MAX_CLIENTS"])
        self.running = True
        print(f"[SERVER] Escuchando en {self.host}:{self.port}")
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.running:
            try:
                csock, addr = self.sock.accept()
                print("[SERVER] Nueva conexión desde", addr)
                threading.Thread(target=self._handle_client, args=(csock,), daemon=True).start()
            except Exception as e:
                print("[SERVER] Error accept:", e)

    def _handle_client(self, csock):
        addr = None
        client_id = None
        buf = b""
        try:
            addr = csock.getpeername()
            while True:
                data = csock.recv(4096)
                if not data:
                    break
                buf += data
                msgs = parse_stream(buf)
                buf = b""
                for msg in msgs:
                    # registro simple
                    if msg.get("type") == "REGISTER":
                        client_id = msg.get("client_id")
                        with self.clients_lock:
                            self.clients[csock] = client_id
                        # confirmar
                        csock.sendall(make_msg({"type":"REGISTERED","client_id":client_id}))
                        # notificar manager
                        try:
                            self.manager.on_client_register(client_id, csock)
                        except:
                            pass
                    else:
                        # delegar al manager
                        try:
                            self.manager.process_message(msg, csock)
                        except Exception as e:
                            print("[SERVER] Error procesando mensaje:", e)
        except Exception as e:
            print(f"[SERVER] Error en cliente {addr}: {e}")
        finally:
            print(f"[SERVER] Cerrando conexión {addr}")
            with self.clients_lock:
                self.clients.pop(csock, None)
            try:
                self.manager.on_client_disconnect(client_id, csock)
            except:
                pass
            try:
                csock.close()
            except:
                pass

    def send(self, csock, obj):
        try:
            csock.sendall(make_msg(obj))
        except Exception:
            pass

    def broadcast(self, obj):
        with self.clients_lock:
            for csock in list(self.clients.keys()):
                try:
                    csock.sendall(make_msg(obj))
                except:
                    # se limpiará en el hilo que detecte la desconexión
                    pass

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        with self.clients_lock:
            for csock in list(self.clients.keys()):
                try:
                    csock.close()
                except:
                    pass
        print("[SERVER] Detenido.")
