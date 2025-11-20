# server/games/rat_race.py
"""
Servidor mantiene snapshot de posiciones y broadcast a clientes.
Cada actualización desde clientes se comparte con todos.
"""
import threading
from common.messages import *
from common.protocol import make_msg

class RatRaceGame:
    def __init__(self, manager):
        self.manager = manager
        self.positions = {}  # client_id -> {mouse_id: pos}
        self.lock = threading.Lock()

    def process(self, msg, csock):
        typ = msg.get("type")
        if typ == MSG_RACE_UPDATE:
            client_id = msg.get("client_id")
            mouse_id = msg.get("mouse_id")
            pos = int(msg.get("pos", 0))
            with self.lock:
                self.positions.setdefault(client_id, {})[mouse_id] = pos
            # Broadcast estado actual
            payload = {"type": MSG_GAME_STATE, "game": "RACE", "positions": self.positions}
            self.manager.server.broadcast(payload)

    def on_disconnect(self, client_id):
        with self.lock:
            if client_id in self.positions:
                self.positions.pop(client_id, None)
        payload = {"type": MSG_GAME_STATE, "game": "RACE", "positions": self.positions}
        try:
            self.manager.server.broadcast(payload)
        except:
            pass
