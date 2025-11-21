# server/games/slots.py
"""
Juego Tragamonedas (Slots).

FUNCIONAMIENTO:
- El cliente envía un mensaje para jugar
- El servidor genera un resultado REAL mediante random.choice
- Evalúa si hay premio:
    • 3 símbolos iguales → 100
    • 2 iguales → 20
    • 0 iguales → 0
- Envía el resultado al cliente
"""

import random
from config.config import CONFIG_PARAMS
from common.messages import *
from common.protocol import make_msg

# Configuraciones desde config
SYMBOLS = CONFIG_PARAMS["SLOTS_SYMBOLS"]
REELS = CONFIG_PARAMS["SLOTS_REELS"]

class SlotsGame:
    def __init__(self, manager):
        self.manager = manager

    def process(self, msg, csock):
        """
        Procesa una jugada simple de slots:
        - Genera un resultado aleatorio REAL
        - Calcula premio
        - Envía respuesta al cliente
        """
        client_id = msg.get("client_id")

        # Crear resultado de cada carrete
        result = [random.choice(SYMBOLS) for _ in range(REELS)]

        # Evaluar premio
        win = 0
        if len(set(result)) == 1:  # todos iguales
            win = 100
        elif len(set(result)) == 2:  # 2 iguales
            win = 20

        # Log en servidor
        print(f"[SLOTS] Cliente {client_id} → Resultado: {result} | Premio: {win}")

        # Enviar resultado al cliente
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
