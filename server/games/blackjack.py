# server/games/blackjack.py
"""
Blackjack multijugador: controlado enteramente por el servidor.

FUNCIONALIDAD:
- Los clientes envían: JOIN, START, ACTION(HIT/STAND)
- El servidor:
    • reparte cartas
    • controla turnos
    • verifica bust
    • maneja dealer
    • envía resultados al final
"""

from common.colors import Color
import threading
from server.utils.helpers import shuffle_deck, hand_value
from common.messages import *
from common.protocol import make_msg

class BlackjackGame:
    def __init__(self, manager):
        """
        players = { client_id : {"sock":socket, "hand":[..], "active":True} }
        deck = mazo actual
        dealer = {"hand":[..]}
        turn_order = lista de turnos en orden de llegada
        """
        self.manager = manager
        self.lock = threading.Lock()
        self.players = {}
        self.deck = []
        self.dealer = {"hand": []}
        self.turn_order = []
        self.current_turn = 0
        self.started = False

    def process(self, msg, csock):
        """
        Procesa mensaje internacional enviado desde el cliente.
        """
        typ = msg.get("type")
        client_id = msg.get("client_id")

        print(f"{Color.MAGENTA}[BJ]{Color.RESET} Acción: {typ} de {client_id}")

        if typ == MSG_BJ_JOIN:
            self.join(client_id, csock)

        elif typ == MSG_BJ_START:
            self.start_game()

        elif typ == MSG_BJ_ACTION:
            action = msg.get("action")
            self.player_action(client_id, action)

    def join(self, client_id, csock):
        """
        Añade a un jugador a la mesa de blackjack.
        """
        with self.lock:
            if client_id in self.players:
                return

            self.players[client_id] = {
                "sock": csock,
                "hand": [],
                "active": True
            }

        print(f"[BJ] {client_id} se unió a la mesa")
        self._broadcast({
            "type": MSG_BJ_UPDATE,
            "msg": f"{client_id} se unió"
        })

    def start_game(self):
        """
        Inicia ronda: reparte cartas y define orden de turnos.
        """
        with self.lock:
            if self.started:
                print("[BJ] Ya hay una ronda iniciada")
                return

            if len(self.players) < 1:
                print("[BJ] No hay jugadores")
                return

            print("[BJ] Iniciando ronda")

            self.deck = shuffle_deck()
            self.dealer["hand"] = []

            # Repartir 2 cartas a cada jugador
            for pid, info in self.players.items():
                info["hand"] = [self.deck.pop(), self.deck.pop()]
                info["active"] = True
                print(f"[BJ] Mano inicial {pid}: {info['hand']}")

            # Dealer también recibe 2
            self.dealer["hand"] = [self.deck.pop(), self.deck.pop()]
            print(f"[BJ] Dealer muestra: {self.dealer['hand'][0]}")

            self.turn_order = list(self.players.keys())
            self.current_turn = 0
            self.started = True

        # Enviar manos iniciales
        for pid, info in self.players.items():
            try:
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_DEAL,
                    "to": pid,
                    "hand": info["hand"],
                    "dealer_show": self.dealer["hand"][0]
                }))
            except Exception as e:
                print("[BJ] Error enviando mano inicial:", e)

        # Iniciar turnos
        self._prompt_current_player()

    def _prompt_current_player(self):
        """
        Notifica al jugador cuyo turno corresponde.
        """
        while True:
            with self.lock:
                if self.current_turn >= len(self.turn_order):
                    # turno del dealer
                    print("[BJ] Dealer juega")
                    threading.Thread(target=self._finish_round, daemon=True).start()
                    return

                pid = self.turn_order[self.current_turn]
                info = self.players.get(pid)

                if not info or not info["active"]:
                    self.current_turn += 1
                    continue

                print(f"[BJ] Turno de {pid}")

            # Enviar mensaje al jugador:
            try:
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_UPDATE,
                    "msg": "Tu turno",
                    "action": "REQUEST"
                }))
            except:
                with self.lock:
                    info["active"] = False
                    self.current_turn += 1
                continue

            return

    def player_action(self, client_id, action):
        """
        Procesa acción HIT o STAND del jugador actual.
        """
        with self.lock:
            info = self.players.get(client_id)
            if not info:
                print("[BJ] Jugador desconocido")
                return

        if action == "HIT":
            with self.lock:
                if not self.deck:
                    self.deck = shuffle_deck()

                card = self.deck.pop()
                info["hand"].append(card)
                print(f"[BJ] {client_id} recibe {card}")

            try:
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_DEAL,
                    "to": client_id,
                    "hand": [card]
                }))
            except:
                pass

            # ¿Se pasó?
            if hand_value(info["hand"]) > 21:
                with self.lock:
                    info["active"] = False
                    self.current_turn += 1

                print("[BJ] BUST")
                info["sock"].sendall(make_msg({"type": MSG_BJ_UPDATE, "msg": "BUST"}))
                self._prompt_current_player()

        elif action == "STAND":
            with self.lock:
                info["active"] = False
                self.current_turn += 1
            print(f"[BJ] {client_id} STAND")
            self._prompt_current_player()

    def _finish_round(self):
        """
        Lógica del dealer + cálculo del resultado final.
        """
        print("[BJ] Dealer juega...")

        while hand_value(self.dealer["hand"]) < 17:
            with self.lock:
                if not self.deck:
                    self.deck = shuffle_deck()
                card = self.deck.pop()
                self.dealer["hand"].append(card)
            print(f"[BJ] Dealer toma: {card}")

        dealer_val = hand_value(self.dealer["hand"])
        print("[BJ] Dealer final:", self.dealer["hand"], dealer_val)

        results = {}

        # Comparar jugador vs dealer
        with self.lock:
            for pid, info in self.players.items():
                val = hand_value(info["hand"])

                if val > 21:
                    res = "LOSE"
                elif dealer_val > 21:
                    res = "WIN"
                elif val > dealer_val:
                    res = "WIN"
                elif val < dealer_val:
                    res = "LOSE"
                else:
                    res = "PUSH"

                results[pid] = {
                    "player": val,
                    "dealer": dealer_val,
                    "result": res
                }

                print(f"[BJ] Resultado {pid}: {res}")

        # Enviar resultados a cada jugador
        for pid, info in self.players.items():
            try:
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_RESULT,
                    "result": results.get(pid),
                    "dealer_hand": self.dealer["hand"]
                }))
            except:
                pass

        print("[BJ] Ronda terminada")

        # Reiniciar estado
        with self.lock:
            self.started = False
            self.players = {}
            self.deck = []
            self.dealer = {"hand": []}
            self.turn_order = []
            self.current_turn = 0

    def _broadcast(self, msg):
        """
        Envía un mensaje a todos los jugadores en la mesa.
        """
        for pid, info in self.players.items():
            try:
                info["sock"].sendall(make_msg(msg))
            except:
                pass

    def on_disconnect(self, client_id):
        """
        Limpia datos del jugador desconectado.
        """
        with self.lock:
            if client_id in self.players:
                print(f"[BJ] {client_id} dejó la mesa")
                self.players.pop(client_id)
