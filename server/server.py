# server/server.py
import socket
import threading
from config.config import CONFIG_PARAMS
from common.utils import make_msg, parse_stream

class RaceServer:
    def __init__(self, host=None, port=None):
        host = host or CONFIG_PARAMS["SERVER_IP_ADDRESS"]
        port = port or CONFIG_PARAMS["SERVER_PORT"]

        self.host = host
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.clients = {}
        self.clients_lock = threading.Lock()

        self.positions = {}
        self.positions_lock = threading.Lock()

        self.running = False

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(CONFIG_PARAMS["SERVER_MAX_CLIENTS"])
        self.running = True
        print(f"[SERVER] Escuchando en {self.host}:{self.port}")
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        while self.running:
            try:
                client_sock, addr = self.sock.accept()
                with self.clients_lock:
                    self.clients[client_sock] = (addr, None)
                print("[SERVER] Nueva conexión:", addr)
                threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
            except Exception as e:
                print("Error accepting:", e)

    def handle_client(self, client_sock):
        addr = client_sock.getpeername()
        buffer = b""
        try:
            while True:
                data = client_sock.recv(4096)
                if not data:
                    break
                buffer += data
                messages = parse_stream(buffer)
                buffer = b""
                for msg in messages:
                    self.process_msg(msg, client_sock)
        except Exception as e:
            print("Error con cliente:", addr, e)
        finally:
            self.remove_client(client_sock)

    def process_msg(self, msg, client_sock):
        mtype = msg.get("type")
        if mtype == "REGISTER":
            client_id = msg.get("client_id")
            with self.clients_lock:
                self.clients[client_sock] = (client_sock.getpeername(), client_id)
            with self.positions_lock:
                self.positions.setdefault(client_id, {})
            try:
                client_sock.sendall(make_msg({"type": "REGISTERED", "client_id": client_id}))
            except:
                pass
        elif mtype == "MOUSE_UPDATE":
            cid = msg.get("client_id")
            mid = msg.get("mouse_id")
            pos = int(msg.get("pos", 0))
            with self.positions_lock:
                self.positions.setdefault(cid, {})
                self.positions[cid][mid] = pos
            self.broadcast_positions()
        elif mtype == "PING":
            try:
                client_sock.sendall(make_msg({"type":"PONG"}))
            except:
                pass

    def broadcast_positions(self):
        with self.positions_lock:
            snapshot = {cid: mice.copy() for cid, mice in self.positions.items()}
        payload = make_msg({"type": "POSITIONS", "positions": snapshot})
        with self.clients_lock:
            for sock in list(self.clients.keys()):
                try:
                    sock.sendall(payload)
                except:
                    self.remove_client(sock)

    def remove_client(self, client_sock):
        with self.clients_lock:
            info = self.clients.pop(client_sock, None)
        if info:
            addr, cid = info
            if cid:
                with self.positions_lock:
                    self.positions.pop(cid, None)
        try:
            client_sock.close()
        except:
            pass
        # broadcast updated positions to remaining clients
        try:
            self.broadcast_positions()
        except:
            pass

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        with self.clients_lock:
            for c in list(self.clients.keys()):
                try:
                    c.close()
                except:
                    pass
