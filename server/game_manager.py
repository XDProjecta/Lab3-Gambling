# server/game_manager.py
"""
GameManager básico: coordina los 3 juegos. 
No usamos salas: un juego activo a la vez por tipo.
Cada juego corre su propia lógica y usa hilos internos cuando aplica.
"""
import threading
from server.games.rat_race import RatRaceGame
from server.games.blackjack import BlackjackGame
from server.games.slots import SlotsGame
from common.messages import *
from common.protocol import make_msg

class GameManager:
    def __init__(self, server):
        self.server = server
        self.lock = threading.Lock()
        self.race = RatRaceGame(self)
        self.blackjack = BlackjackGame(self)
        self.slots = SlotsGame(self)

    def on_client_register(self, client_id, csock):
        # Enviar lista de juegos correctamente serializada
        try:
            msg = {"type": MSG_GAME_LIST, "games": ["RACE", "BLACKJACK", "SLOTS"]}
            csock.sendall(make_msg(msg))
        except Exception as e:
            print("[SERVER] Error enviando GAME_LIST:", e)

    def on_client_disconnect(self, client_id, csock):
        try: self.race.on_disconnect(client_id)
        except: pass
        try: self.blackjack.on_disconnect(client_id)
        except: pass
        try: self.slots.on_disconnect(client_id)
        except: pass

    def process_message(self, msg, csock):
        typ = msg.get("type")

        if typ in (MSG_RACE_UPDATE, MSG_RACE_ACTION):
            self.race.process(msg, csock)
            return

        if typ in (MSG_BJ_JOIN, MSG_BJ_START, MSG_BJ_ACTION):
            self.blackjack.process(msg, csock)
            return

        if typ == MSG_SLOTS_SPIN:
            self.slots.process(msg, csock)
            return

        # fallback con serialización correcta
        try:
            csock.sendall(make_msg({"type": MSG_INFO, "msg": "Mensaje no reconocido por el servidor."}))
        except:
            pass
