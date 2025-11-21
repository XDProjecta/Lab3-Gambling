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

        # si el tipo de mensaje es MSG_BJ_JOIN, entonces llamamos a la función join
        if typ == MSG_BJ_JOIN:
            # llamamos a la función join para que el jugador se una a la mesa
            self.join(client_id, csock)

        elif typ == MSG_BJ_START:
            # si el mensaje es MSG_BJ_START, entonces iniciamos el juego
            self.start_game()

        elif typ == MSG_BJ_ACTION:
            # si el mensaje es MSG_BJ_ACTION, entonces procesamos la acción del jugador
            action = msg.get("action")
            # llamamos a la función player_action para procesar la acción del jugador
            self.player_action(client_id, action)

    def join(self, client_id, csock):
        """
        Añade a un jugador a la mesa de blackjack.
        """
        # si el jugador ya está en la mesa, no hacer nada
        with self.lock:
            if client_id in self.players:
                return
        # si no, agregarlo por medio de su client_id y socket
            self.players[client_id] = {
                "sock": csock,
                "hand": [],
                "active": True
            }
        # Log en servidor
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
            # si el juego ya empezó, no hacer nada
            if self.started:
                print("[BJ] Ya hay una ronda iniciada")
                return
            # si no hay jugadores, no iniciar
            if len(self.players) < 1:
                print("[BJ] No hay jugadores")
                return

            print("[BJ] Iniciando ronda")
            # Inicializar mazo y manos 
            self.deck = shuffle_deck()
            self.dealer["hand"] = []

            # Repartir 2 cartas a cada jugador
            # para cada jugador en la mesa
            for pid, info in self.players.items():
                # su mano inicial son 2 cartas del mazo
                info["hand"] = [self.deck.pop(), self.deck.pop()]
                # marcar como activo el jugador
                info["active"] = True
                # log en servidor
                print(f"[BJ] Mano inicial {pid}: {info['hand']}")

            # Dealer también recibe 2 por medio de una nueva lista
            self.dealer["hand"] = [self.deck.pop(), self.deck.pop()]
            # se muestra solo una carta del dealer, esa es la visible para los jugadores
            print(f"[BJ] Dealer muestra: {self.dealer['hand'][0]}")

            # Definir orden de turnos
            self.turn_order = list(self.players.keys())
            # reiniciar turno actual
            self.current_turn = 0
            # marcar juego como iniciado
            self.started = True

        # Enviar manos iniciales
        # para cada jugador en la mesa
        for pid, info in self.players.items():
            try:
                # enviamos la mano inicial al jugador por medio de su socket
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_DEAL,
                    "to": pid,
                    "hand": info["hand"],
                    # la carta visible del dealer
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
                # si ya pasamos por todos los jugadores
                if self.current_turn >= len(self.turn_order):
                    # turno del dealer
                    print("[BJ] Dealer juega")
                    # iniciar hilo para no bloquear el servidor
                    threading.Thread(target=self._finish_round, daemon=True).start()
                    return
                # obtener el client_id del jugador actual
                pid = self.turn_order[self.current_turn]
                # obtener info del jugador actual
                info = self.players.get(pid)
                # si el jugador no está activo, saltar su turno
                if not info or not info["active"]:
                    self.current_turn += 1
                    continue
                # turno encontrado, imprimir en log
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
                    # si hubo error, marcar jugador como inactivo y pasar turno
                    info["active"] = False
                    self.current_turn += 1
                continue

            return

    def player_action(self, client_id, action):
        """
        Procesa acción HIT o STAND del jugador actual.
        """
        with self.lock:
            # si el jugador no está en la mesa, ignorar
            info = self.players.get(client_id)
            if not info:
                print("[BJ] Jugador desconocido")
                return

        if action == "HIT":
            # si el jugador pidió HIT, darle una carta
            with self.lock:
                if not self.deck:
                    self.deck = shuffle_deck()
            # de la baraja, sacar una carta
                card = self.deck.pop()
                # añadir carta a la mano del jugador
                info["hand"].append(card)
                # log en servidor
                print(f"[BJ] {client_id} recibe {card}")

            try:
                # enviar carta al jugador
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
                    # si se pasó, marcar como inactivo y pasar turno
                    info["active"] = False
                    self.current_turn += 1
            # mostrar mensaje de BUST
                print("[BJ] BUST")
                # mostrar mensaje al jugador y pedir siguiente turno
                info["sock"].sendall(make_msg({"type": MSG_BJ_UPDATE, "msg": "BUST"}))
                # pasar al siguiente jugador
                self._prompt_current_player()

        # si el jugador pidió STAND, simplemente pasar turno, lo marcamos como inactivo
        elif action == "STAND":
            with self.lock:
                info["active"] = False
                self.current_turn += 1
            print(f"[BJ] {client_id} STAND")
            # pasar al siguiente jugador
            self._prompt_current_player()

    def _finish_round(self):
        """
        Lógica del dealer + cálculo del resultado final.
        """
        print("[BJ] Dealer juega...")
        # el dealer toma cartas hasta llegar a 17 o más, nunca menos de 17
        while hand_value(self.dealer["hand"]) < 17:
            with self.lock:
                if not self.deck:
                    # si el mazo está vacío, barajar uno nuevo
                    self.deck = shuffle_deck()
                    # sacar una carta del mazo
                card = self.deck.pop()
                # añadir carta a la mano del dealer
                self.dealer["hand"].append(card)
                # mostrar carta tomada por el dealer
            print(f"[BJ] Dealer toma: {card}")
        # valor final del dealer
        dealer_val = hand_value(self.dealer["hand"])
        # mostrar valor final del dealer
        print("[BJ] Dealer final:", self.dealer["hand"], dealer_val)

        results = {}

        # Comparar jugador vs dealer
        with self.lock:
            # para cada jugador en la mesa
            for pid, info in self.players.items():
                # valor de la mano del jugador
                val = hand_value(info["hand"])
            # si dicho valor es mayor a 21, pierde
                if val > 21:
                    res = "LOSE"
                    # si el dealer se pasó, el jugador gana
                elif dealer_val > 21:
                    res = "WIN"
                    # si ninguno se pasó, comparar valores
                elif val > dealer_val:
                    # si el jugador tiene más, gana
                    res = "WIN"
                elif val < dealer_val:
                    # si el dealer tiene más, pierde
                    res = "LOSE"
                else:
                    # si hay empate, es PUSH
                    res = "PUSH"

                results[pid] = {
                    "player": val,
                    "dealer": dealer_val,
                    "result": res
                }
                # imprimir resultado en servidor
                print(f"[BJ] Resultado {pid}: {res}")

        # Enviar resultados a cada jugador por medio de su socket
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

        # Reiniciar estado para próxima ronda
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
