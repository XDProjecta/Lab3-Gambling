# server/games/rat_race.py
"""
Lógica del juego "Carrera de Ratones" (Rat Race).

FUNCIONALIDAD:
- Cada cliente elige un ratón (m1, m2, m3...)
- El cliente envía periódicamente la posición de *su propio ratón*
- El servidor guarda posiciones de cada jugador
- Cuando un ratón llega a la meta → se marca como terminado
- Cuando TODOS los ratones seleccionados llegan → se calcula el ranking
- Se envía un mensaje individual a cada jugador indicando su puesto

IMPORTANTE:
Este módulo NO mueve ratones automáticamente; depende de actualizaciones enviadas desde los clientes.
"""

import time
from common.messages import *
from common.protocol import make_msg
from config.config import CONFIG_PARAMS

class RatRaceGame:
    def __init__(self, manager):
        """
        Inicializa el estado del juego:
        - selected_mouse: {client_id: "m1" ...}
        - positions: {client_id: posición}
        - finished: {client_id: timestamp}
        """
        self.manager = manager
        self.lock = manager.lock

        self.selected_mouse = {}
        self.positions = {}
        self.finished = {}

        self.race_length = CONFIG_PARAMS["RACE_LENGTH"]
        self.last_update = {}  # throttling por cliente

    def process(self, msg, csock):
        """
        Recibe mensajes que vienen del GameManager.

        Tipos:
        - "RACE_SELECT": cliente elige ratón
        - MSG_RACE_UPDATE: cliente envía nueva posición
        """
        typ = msg.get("type")

        # 1. El jugador eligió su ratón
        if typ == "RACE_SELECT":
            client_id = msg["client_id"]
            mouse = msg["mouse_id"]

            with self.lock:
                self.selected_mouse[client_id] = mouse
                self.positions[client_id] = 0

            print(f"[RACE] {client_id} eligió {mouse}")
            return

        # 2. Actualización de posiciones
        if typ == MSG_RACE_UPDATE:
            self.handle_update(msg, csock)

    def handle_update(self, msg, csock):
        """
        Maneja actualizaciones enviadas desde el cliente.
        El mensaje contiene:
        - client_id
        - pos (nueva posición del ratón)
        """
        client_id = msg["client_id"]
        pos = int(msg["pos"])

        # Si el cliente no seleccionó ratón, ignorar
        if client_id not in self.selected_mouse:
            return

        # Control de spam: máximo una actualización cada 70 ms
        now = time.time()
        if now - self.last_update.get(client_id, 0) < 0.07:
            return
        self.last_update[client_id] = now

        with self.lock:
            # Ya había terminado → ignorar
            if client_id in self.finished:
                return

            # Si alcanza la meta
            if pos >= self.race_length:
                pos = self.race_length
                self.positions[client_id] = pos
                self.finished[client_id] = now

                print(f"[RACE] {client_id} llegó a meta")

                # Si todos los participantes terminaron → FIN DE LA CARRERA
                if len(self.finished) == len(self.positions):
                    self.end_race()

            else:
                self.positions[client_id] = pos

        # Broadcast del estado general a todos los clientes
        self.manager.server.broadcast({
            "type": MSG_GAME_STATE,
            "game": "RACE",
            "positions": self.positions
        })

    def end_race(self):
        """
        Calcula el ranking final por tiempo de llegada.
        Envía un mensaje individual a cada jugador indicando su posición.
        """
        # Ordenar por timestamp
        ranking = sorted(self.finished.items(), key=lambda x: x[1])
        ordered = [r[0] for r in ranking]

        print("[RACE] Carrera terminada:", ordered)

        # Enviar ranking a cada jugador
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
        """
        Limpia datos cuando un jugador se desconecta.
        """
        with self.lock:
            self.selected_mouse.pop(client_id, None)
            self.positions.pop(client_id, None)
            self.finished.pop(client_id, None)
