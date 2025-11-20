# server/games/slots.py

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

        # generar resultado REAL
        result = [random.choice(SYMBOLS) for _ in range(REELS)]

        # calcular premio
        win = 0
        if len(set(result)) == 1:
            win = 100
        elif len(set(result)) == 2:
            win = 20

        # Log del servidor
        print(f"[SLOTS] Cliente {client_id} → Resultado: {result} | Premio: {win}")

        # enviar a cliente
        payload = {
            "type": MSG_SLOTS_RESULT,
            "client_id": client_id,
            "result": result,
            "win": win
        }

        try:
            csock.sendall(make_msg(payload))
        except:
            print("[SLOTS] Error enviando resultado al cliente.")
