# server/game_manager.py
"""
GameManager
-----------
Este módulo actúa como EL CEREBRO CENTRAL del servidor.

FUNCIONES PRINCIPALES:
- Recibe los mensajes que llegan desde Server._handle_client()
- Determina a qué juego pertenece el mensaje
- Redirige el mensaje al módulo de juego correspondiente:
    • Rat Race
    • Slots
    • Blackjack

Además, maneja:
- El registro de jugadores
- La desconexión de jugadores
- Protección con locks para evitar condiciones de carrera

Es decir:
El Server recibe --> GameManager decide --> Juego procesa
"""

from common.messages import *
from server.games.rat_race import RatRaceGame
from server.games.slots import SlotsGame
from server.games.blackjack import BlackjackGame
import threading

class GameManager:
    def __init__(self, server):
        """
        Inicializa el GameManager e instancia cada juego.
        
        - server: referencia al Server principal.
        - lock: lock global utilizado por los juegos para evitar condiciones
                de carrera cuando múltiples hilos escriben al mismo tiempo.
        """
        self.server = server
        self.lock = threading.Lock()

        # Instancias de todos los juegos disponibles
        self.rat_race = RatRaceGame(self)
        self.slots = SlotsGame(self)
        self.blackjack = BlackjackGame(self)

    # ----------------------------------------------------------------------
    # REGISTRO Y DESCONEXIÓN
    # ----------------------------------------------------------------------

    def on_client_register(self, client_id, csock):
        """
        Notificado por Server cuando un nuevo cliente se registra.
        Puede ser usado para inicializar datos globales si fuera necesario.
        """
        print(f"[GM] Cliente registrado: {client_id}")

    def on_client_disconnect(self, client_id, csock):
        """
        LLAMADO cuando un cliente se desconecta.
        
        Aquí notificamos a CADA JUEGO que el cliente ya no está presente.
        Esto es importante porque:
        - Rat Race puede tener ratones asignados a ese cliente
        - Blackjack puede tener manos activas
        """
        print(f"[GM] Cliente desconectado: {client_id}")

        # cada juego debe limpiar sus datos internos
        try: self.rat_race.on_disconnect(client_id)
        except: pass

        try: self.blackjack.on_disconnect(client_id)
        except: pass

        # slots no necesita limpieza porque no mantiene estado por jugador

    # ----------------------------------------------------------------------
    # PROCESAMIENTO GENERAL DE MENSAJES
    # ----------------------------------------------------------------------

    def process_message(self, msg, csock):
        """
        Decide a qué juego pertenece un mensaje.

        Cada mensaje que llega tiene:
            msg["type"]  → tipo de evento
            msg["client_id"]  → quién lo envió

        Este método NO procesa mensajes directamente, 
        sino que los ENVÍA al módulo de juego correcto.
        """

        typ = msg.get("type")

        # --------------------------
        # MENSAJES DE RAT RACE
        # --------------------------
        if typ in ("RACE_SELECT", MSG_RACE_UPDATE):
            self.rat_race.process(msg, csock)
            return

        # --------------------------
        # MENSAJES DE SLOTS
        # --------------------------
        if typ == MSG_SLOTS_SPIN:
            self.slots.process(msg, csock)
            return

        # --------------------------
        # MENSAJES DE BLACKJACK
        # --------------------------
        if typ in (MSG_BJ_JOIN, MSG_BJ_START, MSG_BJ_ACTION):
            self.blackjack.process(msg, csock)
            return

        # --------------------------
        # MENSAJE NO RECONOCIDO
        # --------------------------
        print(f"[GM] Mensaje desconocido recibido: {msg}")
