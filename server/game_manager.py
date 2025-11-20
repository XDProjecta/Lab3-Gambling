"""
server/game_manager.py
GameManager 
Coordina los 3 juegos.
"""
from common.colors import Color
from server.games.rat_race import RatRaceGame
from server.games.blackjack import BlackjackGame
from server.games.slots import SlotsGame
from common.messages import *
from common.protocol import make_msg
import threading

class GameManager:
    def __init__(self, server):
        self.server = server
        self.lock = threading.Lock()
        self.race = RatRaceGame(self)
        self.blackjack = BlackjackGame(self)
        self.slots = SlotsGame(self)

    def on_client_register(self, client_id, csock):
        print(f"{Color.CYAN}[SERVER][REGISTER]{Color.RESET} Nuevo cliente: {client_id}")
        try:
            msg = {"type": MSG_GAME_LIST, "games": ["RACE", "BLACKJACK", "SLOTS"]}
            csock.sendall(make_msg(msg))
        except Exception as e:
            print(f"{Color.RED}[SERVER] Error enviando GAME_LIST:{Color.RESET}", e)

    def on_client_disconnect(self, client_id, csock):
        print(f"{Color.YELLOW}[SERVER][DISCONNECT]{Color.RESET} Cliente se fue: {client_id}")
        try: self.race.on_disconnect(client_id)
        except: pass
        try: self.blackjack.on_disconnect(client_id)
        except: pass
        try: self.slots.on_disconnect(client_id)
        except: pass

    def process_message(self, msg, csock):
        typ = msg.get("type")
        client = msg.get("client_id")

        print(f"{Color.CYAN}[SERVER][MSG]{Color.RESET} tipo={typ} desde {client} → {msg}")

        if typ in (MSG_RACE_UPDATE, MSG_RACE_ACTION):
            self.race.process(msg, csock); return

        if typ in (MSG_BJ_JOIN, MSG_BJ_START, MSG_BJ_ACTION):
            self.blackjack.process(msg, csock); return

        if typ == MSG_SLOTS_SPIN:
            self.slots.process(msg, csock); return

        try:
            csock.sendall(make_msg({"type": MSG_INFO, "msg": "Mensaje no reconocido."}))
        except:
            print(f"{Color.RED}Error enviando fallback{Color.RESET}")
