# server/games/blackjack.py
"""
Blackjack multijugador con logs robustos y manejo de errores.
Soporta JOIN, START y ACTION (HIT / STAND). Turnos controlados por servidor.
"""
from common.colors import Color
import threading
from server.utils.helpers import shuffle_deck, hand_value
from common.messages import *
from common.protocol import make_msg

class BlackjackGame:
    def __init__(self, manager):
        self.manager = manager
        self.lock = threading.Lock()
        self.players = {}        # client_id -> {"sock": csock, "hand": [], "active": True}
        self.deck = []
        self.dealer = {"hand": []}
        self.turn_order = []
        self.current_turn = 0
        self.started = False

    def process(self, msg, csock):
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
        with self.lock:
            if client_id in self.players:
                return
            self.players[client_id] = {"sock": csock, "hand": [], "active": True}

        print(f"{Color.MAGENTA}[BJ] {client_id} se unió a la mesa{Color.RESET}")
        self._broadcast({"type": MSG_BJ_UPDATE, "msg": f"{client_id} se unió"})

    def start_game(self):
        with self.lock:
            if self.started:
                print(f"{Color.MAGENTA}[BJ] Ya hay una ronda iniciada{Color.RESET}")
                return
            if len(self.players) < 1:
                print(f"{Color.MAGENTA}[BJ] No hay jugadores para iniciar la ronda{Color.RESET}")
                return

            print(f"{Color.MAGENTA}[BJ] Iniciando nueva ronda{Color.RESET}")

            self.deck = shuffle_deck()
            self.dealer["hand"] = []

            # repartir dos cartas a cada jugador
            for pid, info in self.players.items():
                info["hand"] = [self.deck.pop(), self.deck.pop()]
                info["active"] = True
                print(f"{Color.MAGENTA}[BJ] Mano inicial {pid}: {info['hand']}{Color.RESET}")

            # dealer
            self.dealer["hand"] = [self.deck.pop(), self.deck.pop()]
            print(f"{Color.YELLOW}[BJ] Dealer muestra: {self.dealer['hand'][0]}{Color.RESET}")

            self.turn_order = list(self.players.keys())
            self.current_turn = 0
            self.started = True

        # enviar manos iniciales (cada jugador recibe su mano)
        for pid, info in list(self.players.items()):
            try:
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_DEAL,
                    "to": pid,
                    "hand": info["hand"],
                    "dealer_show": self.dealer["hand"][0]
                }))
            except Exception as e:
                print(f"{Color.RED}[BJ] Error enviando mano inicial a {pid}: {e}{Color.RESET}")

        # iniciar ciclo de turnos
        self._prompt_current_player()

    def _prompt_current_player(self):
        # buscamos el siguiente jugador activo; si ninguno, lanzamos dealer
        while True:
            with self.lock:
                if self.current_turn >= len(self.turn_order):
                    # todos los turnos procesados -> dealer juega
                    print(f"{Color.YELLOW}[BJ] Fin de turnos → Dealer juega{Color.RESET}")
                    threading.Thread(target=self._finish_round, daemon=True).start()
                    return

                pid = self.turn_order[self.current_turn]
                info = self.players.get(pid)

                if not info or not info.get("active", False):
                    # saltar inactivos
                    self.current_turn += 1
                    continue

                # pedir acción al jugador actual
                print(f"{Color.MAGENTA}[BJ] Turno de {pid}{Color.RESET}")

            # fuera del lock hacemos el send para evitar bloqueos largos
            try:
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_UPDATE,
                    "msg": "Tu turno",
                    "action": "REQUEST"
                }))
            except Exception as e:
                print(f"{Color.RED}[BJ] Error pidiendo turno a {pid}: {e}{Color.RESET}")
                # marcar jugador como inactivo y seguir
                with self.lock:
                    info["active"] = False
                    self.current_turn += 1
                continue

            # si se pudo pedir turno, salimos hasta recibir acción (player_action avanzará current_turn)
            return

    def player_action(self, client_id, action):
        # recibe la acción de un jugador durante su turno
        with self.lock:
            info = self.players.get(client_id)
            if not info:
                print(f"{Color.RED}[BJ] Acción de jugador desconocido: {client_id}{Color.RESET}")
                return
            if not info.get("active", False):
                print(f"{Color.YELLOW}[BJ] Acción ignorada, {client_id} no está activo{Color.RESET}")
                return

            print(f"{Color.MAGENTA}[BJ] {client_id} → {action}{Color.RESET}")

        if action == "HIT":
            # repartir carta
            with self.lock:
                if not self.deck:
                    self.deck = shuffle_deck()
                card = self.deck.pop()
                info["hand"].append(card)
                print(f"{Color.MAGENTA}[BJ] {client_id} recibe: {card}{Color.RESET}")

            try:
                info["sock"].sendall(make_msg({"type": MSG_BJ_DEAL, "to": client_id, "hand": [card]}))
            except Exception as e:
                print(f"{Color.RED}[BJ] Error enviando carta a {client_id}: {e}{Color.RESET}")

            # comprobar bust
            if hand_value(info["hand"]) > 21:
                with self.lock:
                    info["active"] = False
                    self.current_turn += 1
                print(f"{Color.RED}[BJ] ❌ BUST para {client_id}{Color.RESET}")
                try:
                    info["sock"].sendall(make_msg({"type": MSG_BJ_UPDATE, "msg": "BUST"}))
                except:
                    pass
                # solicitar siguiente jugador
                self._prompt_current_player()
            else:
                # pedir de nuevo (mismo jugador)
                try:
                    info["sock"].sendall(make_msg({"type": MSG_BJ_UPDATE, "msg": "Decide de nuevo", "action": "REQUEST"}))
                except:
                    pass

        elif action == "STAND":
            with self.lock:
                info["active"] = False
                self.current_turn += 1
            print(f"{Color.YELLOW}[BJ] {client_id} se planta{Color.RESET}")
            # solicitar siguiente jugador
            self._prompt_current_player()

        else:
            print(f"{Color.YELLOW}[BJ] Acción desconocida de {client_id}: {action}{Color.RESET}")

    def _finish_round(self):
        print(f"{Color.YELLOW}[BJ] Dealer juega...{Color.RESET}")
        # dealer toma cartas hasta 17
        while hand_value(self.dealer["hand"]) < 17:
            with self.lock:
                if not self.deck:
                    self.deck = shuffle_deck()
                card = self.deck.pop()
                self.dealer["hand"].append(card)
            print(f"{Color.YELLOW}[BJ] Dealer toma: {card}{Color.RESET}")

        dealer_val = hand_value(self.dealer["hand"])
        print(f"{Color.YELLOW}[BJ] Dealer final: {self.dealer['hand']} → {dealer_val}{Color.RESET}")

        results = {}
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

                results[pid] = {"player": val, "dealer": dealer_val, "result": res}
                color = Color.GREEN if res == "WIN" else (Color.RED if res == "LOSE" else Color.YELLOW)
                print(f"{color}[BJ] Resultado {pid}: {res} (Jugador {val} vs Dealer {dealer_val}){Color.RESET}")

        # enviar resultados a cada jugador
        for pid, info in list(self.players.items()):
            try:
                info["sock"].sendall(make_msg({
                    "type": MSG_BJ_RESULT,
                    "result": results.get(pid),
                    "dealer_hand": self.dealer["hand"]
                }))
            except Exception as e:
                print(f"{Color.RED}[BJ] Error enviando resultado a {pid}: {e}{Color.RESET}")

        print(f"{Color.MAGENTA}[BJ] Ronda terminada{Color.RESET}\n")

        # reiniciar mesa
        with self.lock:
            self.started = False
            self.players = {}
            self.deck = []
            self.dealer = {"hand": []}
            self.turn_order = []
            self.current_turn = 0

    def _broadcast(self, obj):
        for pid, info in list(self.players.items()):
            try:
                info["sock"].sendall(make_msg(obj))
            except Exception:
                pass

    def on_disconnect(self, client_id):
        with self.lock:
            if client_id in self.players:
                print(f"{Color.YELLOW}[BJ] {client_id} salió de la mesa{Color.RESET}")
                self.players.pop(client_id, None)
