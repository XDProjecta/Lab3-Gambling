# server/games/rat_race.py

import threading
from common.messages import *
from common.protocol import make_msg
from config.config import CONFIG_PARAMS
from common.colors import Color

FINISH = CONFIG_PARAMS["RACE_LENGTH"]

class RatRaceGame:
    def __init__(self, manager):
        self.manager = manager
        self.positions = {}   # client_id -> {mouse_id: pos}
        self.lock = threading.Lock()
        self.finished_mice = set()   # set of (client_id, mouse_id) that finished
        self.winner_announced = False

    def process(self, msg, csock):
        typ = msg.get("type")
        if typ != MSG_RACE_UPDATE:
            return
        client_id = msg.get("client_id")
        mouse_id = msg.get("mouse_id")
        pos = int(msg.get("pos", 0))
        finish_flag = bool(msg.get("finish", False))

        key = (client_id, mouse_id)
        with self.lock:
            # si esta mezcla ya se marcó como final, ignorar updates extra
            if key in self.finished_mice:
                # opcional: log leve
                # print(f"[RACE] Ignorado update after finish: {client_id} {mouse_id} = {pos}")
                return

            self.positions.setdefault(client_id, {})[mouse_id] = pos

            if finish_flag or pos >= FINISH:
                self.finished_mice.add(key)
                print(f"{Color.ORANGE}[RACE]{Color.RESET} {client_id}::{mouse_id} cruzó la meta con pos={pos}")

        # anunciar si hay ganador absoluto (primera vez)
        if not self.winner_announced:
            winner = self._find_first_finished()
            if winner:
                self.winner_announced = True
                w_client, w_mouse, w_pos = winner
                print(f"{Color.GOLD}{Color.BOLD}🏆 GANADOR: {w_mouse} (jugador {w_client}) pos={w_pos} 🏆{Color.RESET}")

        # construir payload pero: si ya hay ganador absoluto y quieres dejar de spamear,
        # podrías enviar sólo ocasionalmente. Aquí enviamos el estado actual, menos ruido porque cliente throttled.
        payload = {"type": MSG_GAME_STATE, "game": "RACE", "positions": self.positions, "finished": list(self.finished_mice)}
        self.manager.server.broadcast(payload)

    def _find_first_finished(self):
        # buscar el finished_mice con mayor prioridad (el que se agregó primero)
        # dado que usamos set no hay orden; para ser sencillo, encontrar cualquier finished y devolver su pos
        with self.lock:
            if not self.finished_mice:
                return None
            # calcular la finished con mayor pos (opción simple)
            best = None
            for (cid, mid) in self.finished_mice:
                pos = self.positions.get(cid, {}).get(mid, 0)
                if best is None or pos > best[2]:
                    best = (cid, mid, pos)
            return best

    def on_disconnect(self, client_id):
        print(f"{Color.YELLOW}[RACE] Cliente desconectado: {client_id}{Color.RESET}")
        with self.lock:
            self.positions.pop(client_id, None)
        try:
            self.manager.server.broadcast({"type": MSG_GAME_STATE, "game": "RACE", "positions": self.positions})
        except:
            pass
