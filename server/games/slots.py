# server/games/slots.py
from common.colors import Color
import random
from config.config import CONFIG_PARAMS
from common.messages import *
from common.protocol import make_msg

SYMBOLS = CONFIG_PARAMS["SLOTS_SYMBOLS"]
REELS = CONFIG_PARAMS["SLOTS_REELS"]

class SlotsGame:
    def __init__(self, manager):
        self.manager = manager

    def process(self, msg, csock):
        client_id = msg.get("client_id")
        print(f"{Color.BLUE}[SLOTS]{Color.RESET} SPIN recibido de {client_id}")

        result = [random.choice(SYMBOLS) for _ in range(REELS)]

        win = 0
        if all(x == result[0] for x in result):
            win = 100
            print(f"{Color.GREEN}[SLOTS][JACKPOT]{Color.RESET} {client_id} → {result}")
        elif len(set(result)) == 2:
            win = 20
            print(f"{Color.YELLOW}[SLOTS] Dos iguales {Color.RESET}{result}")
        else:
            print(f"{Color.BLUE}[SLOTS] Resultado normal{Color.RESET} {result}")

        payload = {"type": MSG_SLOTS_RESULT, "client_id": client_id, "result": result, "win": win}

        try:
            csock.sendall(make_msg(payload))
            print(f"{Color.BLUE}[SLOTS] Resultado enviado → {result}, Premio={win}")
        except Exception as e:
            print(f"{Color.RED}[SLOTS] Error enviando resultado: {e}{Color.RESET}")

    def on_disconnect(self, client_id):
        print(f"{Color.YELLOW}[SLOTS] Cliente salió {client_id}{Color.RESET}")
