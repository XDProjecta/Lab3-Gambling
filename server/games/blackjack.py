# server/games/blackjack.py
"""
Blackjack multijugador (simple).
- Los jugadores envían JOIN.
- Un jugador puede enviar START para iniciar (servidor reparte).
- Turnos gestionados por el servidor.
- Apuestas/moneda no implementadas (solo resultado).
"""
import threading
from server.utils.helpers import shuffle_deck, hand_value
from common.messages import *
from common.protocol import make_msg

class BlackjackGame:
    def __init__(self, manager):
        self.manager = manager
        self.lock = threading.Lock()
        self.players = {}   # client_id -> {"sock":csock,"hand":[], "active":True}
        self.deck = []
        self.dealer = {"hand": []}
        self.turn_order = []
        self.current_turn = 0
        self.started = False

    def process(self, msg, csock):
        typ = msg.get("type")
        client_id = msg.get("client_id")
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
            # avisar mesa
            self._broadcast({"type": MSG_BJ_UPDATE, "msg": f"{client_id} se unió"})

    def start_game(self):
        with self.lock:
            if self.started:
                return
            if len(self.players) < 1:
                return
            self.deck = shuffle_deck()
            self.dealer["hand"] = []
            # repartir 2 cartas a cada jugador
            for pid, info in self.players.items():
                info["hand"] = [self.deck.pop(), self.deck.pop()]
                info["active"] = True
            # dealer
            self.dealer["hand"] = [self.deck.pop(), self.deck.pop()]
            self.turn_order = list(self.players.keys())
            self.current_turn = 0
            self.started = True
        # enviar manos iniciales
        for pid, info in list(self.players.items()):
            try:
                info["sock"].sendall(make_msg({"type": MSG_BJ_DEAL, "to": pid, "hand": info["hand"], "dealer_show": self.dealer["hand"][0]}))
            except:
                pass
        # solicitar acción al primer jugador
        self._prompt_current_player()

    def _prompt_current_player(self):
        with self.lock:
            if self.current_turn >= len(self.turn_order):
                # terminar
                threading.Thread(target=self._finish_round, daemon=True).start()
                return
            pid = self.turn_order[self.current_turn]
            info = self.players.get(pid)
            if not info or not info["active"]:
                self.current_turn += 1
                self._prompt_current_player()
                return
            try:
                info["sock"].sendall(make_msg({"type": MSG_BJ_UPDATE, "msg": "Tu turno", "action": "REQUEST"}))
            except:
                info["active"] = False
                self.current_turn += 1
                self._prompt_current_player()

    def player_action(self, client_id, action):
        with self.lock:
            info = self.players.get(client_id)
            if not info or not info["active"]:
                return
            if action == "HIT":
                if not self.deck:
                    # rebarajar (simple)
                    self.deck = shuffle_deck()
                card = self.deck.pop()
                info["hand"].append(card)
                try:
                    info["sock"].sendall(make_msg({"type": MSG_BJ_DEAL, "to": client_id, "hand": [card]}))
                except:
                    pass
                if hand_value(info["hand"]) > 21:
                    info["active"] = False
                    try:
                        info["sock"].sendall(make_msg({"type": MSG_BJ_UPDATE, "msg": "BUST"}))
                    except:
                        pass
                    self.current_turn += 1
                    self._prompt_current_player()
                else:
                    try:
                        info["sock"].sendall(make_msg({"type": MSG_BJ_UPDATE, "msg": "Decide de nuevo", "action": "REQUEST"}))
                    except:
                        pass
            elif action == "STAND":
                info["active"] = False
                self.current_turn += 1
                self._prompt_current_player()
            else:
                # ignorar acciones desconocidas
                pass

    def _finish_round(self):
        # dealer juega: hit hasta 17
        while hand_value(self.dealer["hand"]) < 17:
            if self.deck:
                self.dealer["hand"].append(self.deck.pop())
            else:
                break
        dealer_val = hand_value(self.dealer["hand"])
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
        # enviar resultados a cada jugador
        for pid, info in list(self.players.items()):
            try:
                info["sock"].sendall(make_msg({"type": MSG_BJ_RESULT, "result": results.get(pid), "dealer_hand": self.dealer["hand"]}))
            except:
                pass
        # reiniciar mesa
        with self.lock:
            self.started = False
            self.players = {}
            self.deck = []
            self.dealer = {"hand": []}
            self.turn_order = []
            self.current_turn = 0

    def _broadcast(self, obj):
        # enviar mensaje a todos los jugadores actuales
        for pid, info in list(self.players.items()):
            try:
                info["sock"].sendall(make_msg(obj))
            except:
                pass

    def on_disconnect(self, client_id):
        with self.lock:
            if client_id in self.players:
                try:
                    self.players.pop(client_id, None)
                except:
                    pass
