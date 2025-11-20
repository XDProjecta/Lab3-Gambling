# server/games/rat_race.py
"""
Carrera de Ratones mejorada:
- Cada cliente elige un ratón.
- Envía posiciones solo de su ratón.
- Cuando llega a meta deja de enviar.
- El servidor calcula ganador y ranking.
- Envía un mensaje individual a cada jugador.
"""

import time
from common.messages import *
from common.protocol import make_msg
from config.config import CONFIG_PARAMS

class RatRaceGame:
    def __init__(self, manager):
        self.manager = manager
        self.lock = manager.lock

        # client_id -> ratón seleccionado ("m1", "m2", etc.)
        self.selected_mouse = {}

        # client_id -> posición actual
        self.positions = {}

        self.finished = {}       # client_id -> tiempo terminado
        self.race_length =  CONFIG_PARAMS["RACE_LENGTH"]

        self.last_update = {}    # throttling por cliente

    def process(self, msg, csock):
        typ = msg.get("type")

        if typ == "RACE_SELECT":
            client_id = msg["client_id"]
            mouse = msg["mouse_id"]

            with self.lock:
                self.selected_mouse[client_id] = mouse
                self.positions[client_id] = 0

            print(f"[RACE] {client_id} eligió {mouse}")
            return

        if typ == MSG_RACE_UPDATE:
            self.handle_update(msg, csock)

    def handle_update(self, msg, csock):
        client_id = msg["client_id"]
        pos = int(msg["pos"])

        # ignorar si no eligió ratón
        if client_id not in self.selected_mouse:
            return

        # throttle: no más de un update cada 70 ms
        now = time.time()
        if now - self.last_update.get(client_id, 0) < 0.07:
            return
        self.last_update[client_id] = now

        with self.lock:
            # evitar que siga avanzando después de meta
            if client_id in self.finished:
                return

            if pos >= self.race_length:
                pos = self.race_length
                self.positions[client_id] = pos
                self.finished[client_id] = now

                print(f"[RACE] {client_id} llegó a meta")

                # verificar si todos terminaron
                if len(self.finished) == len(self.positions):
                    self.end_race()

            else:
                self.positions[client_id] = pos

        # broadcast estado general (coordenadas)
        self.manager.server.broadcast({
            "type": MSG_GAME_STATE,
            "game": "RACE",
            "positions": self.positions
        })

    def end_race(self):
        # ranking por tiempo de llegada
        ranking = sorted(self.finished.items(), key=lambda x: x[1])
        ordered = [r[0] for r in ranking]

        print("[RACE] carrera terminada:", ordered)

        # a cada jugador enviamos un mensaje individual
        for idx, pid in enumerate(ordered):
            place = idx + 1

            result_msg = {
                "type": "RACE_FINISH",
                "client_id": pid,
                "your_place": place,
                "ranking": ordered
            }

            sock = self.manager.server.clients.get(pid)
            if sock:
                try:
                    sock.sendall(make_msg(result_msg))
                except:
                    pass

    def on_disconnect(self, client_id):
        with self.lock:
            self.selected_mouse.pop(client_id, None)
            self.positions.pop(client_id, None)
            self.finished.pop(client_id, None)
