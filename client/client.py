# client/client.py
import socket
import threading
from config.config import CONFIG_PARAMS
from common.utils import make_msg, parse_stream

class RaceClient:
    def __init__(self, client_id, on_positions_update=None):
        self.client_id = client_id
        self.on_positions_update = on_positions_update
        self.sock = None
        self._recv_thread = None
        self._connected = False
        self._lock = threading.Lock()

    def connect(self, host=None, port=None, timeout=5):
        host = host or CONFIG_PARAMS["SERVER_IP_ADDRESS"]
        port = port or CONFIG_PARAMS["SERVER_PORT"]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))
        self.sock.settimeout(None)
        self._connected = True
        self.send({"type":"REGISTER", "client_id": self.client_id})
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def send(self, obj):
        if not self._connected or self.sock is None:
            return
        try:
            with self._lock:
                self.sock.sendall(make_msg(obj))
        except Exception:
            self.close()

    def _recv_loop(self):
        buf = b""
        try:
            while self._connected:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data
                msgs = parse_stream(buf)
                buf = b""
                for msg in msgs:
                    self._handle_msg(msg)
        except Exception:
            pass
        finally:
            self.close()

    def _handle_msg(self, msg):
        t = msg.get("type")
        if t == "POSITIONS":
            positions = msg.get("positions", {})
            if self.on_positions_update:
                try:
                    self.on_positions_update(positions)
                except:
                    pass

    def send_mouse_update(self, mouse_id, pos):
        self.send({"type":"MOUSE_UPDATE", "client_id": self.client_id, "mouse_id": mouse_id, "pos": pos})

    def close(self):
        self._connected = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
