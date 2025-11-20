# client/client.py
"""
Cliente de red: conecta al servidor y lanza hilo receptor.
Envía REGISTER al conectarse.
"""
import socket
import threading
from common.protocol import make_msg, parse_stream
from config.config import CONFIG_PARAMS

SERVER_IP = CONFIG_PARAMS["SERVER_IP_ADDRESS"]
SERVER_PORT = CONFIG_PARAMS["SERVER_PORT"]

class NetworkClient:
    def __init__(self, client_id, on_message=None):
        self.client_id = client_id
        self.on_message = on_message
        self.sock = None
        self.connected = False
        self._lock = threading.Lock()
        self._recv_thread = None

    def connect(self, host=None, port=None, timeout=5):
        host = host or SERVER_IP
        port = port or SERVER_PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))
        self.sock.settimeout(None)
        self.connected = True
        # register
        self.send({"type":"REGISTER", "client_id": self.client_id})
        # start receive thread
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def send(self, obj: dict):
        if not self.connected:
            return
        try:
            with self._lock:
                self.sock.sendall(make_msg(obj))
        except Exception:
            self.close()

    def _recv_loop(self):
        buf = b""
        try:
            while self.connected:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data
                msgs = parse_stream(buf)
                buf = b""
                for m in msgs:
                    if self.on_message:
                        try:
                            self.on_message(m)
                        except:
                            pass
        except Exception:
            pass
        finally:
            self.close()

    def close(self):
        self.connected = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
