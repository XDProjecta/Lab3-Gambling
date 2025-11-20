# server/games/slots.py
"""
Slots simple en servidor:
- recibe SLOTS_SPIN del cliente, genera resultado y responde.
"""
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
        # generar resultado
        result = [random.choice(SYMBOLS) for _ in range(REELS)]
        # simple política de premios
        win = 0
        if all(x == result[0] for x in result):
            win = 100
        elif len(set(result)) == 2:
            win = 20
        payload = {"type": MSG_SLOTS_RESULT, "client_id": client_id, "result": result, "win": win}
        try:
            csock.sendall(make_msg(payload))
        except:
            pass

    def on_disconnect(self, client_id):
        pass
