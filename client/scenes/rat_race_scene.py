# client/scenes/rat_race_scene.py
"""
RaceScene
---------
Esta escena muestra la Carrera de Ratones del lado del cliente.

FUNCIONALIDAD:
- El usuario elige un ratón (m1, m2, m3...)
- Localmente se mueven TODOS los ratones
- Solo se envía al servidor la posición del ratón seleccionado
- El servidor verifica posiciones → envía GAME_STATE
- Cuando el servidor detecta término → envía RACE_FINISH
- Se muestra un popup con el ranking

NOTA IMPORTANTE:
Este archivo no contiene bots.
Los bots viven en el servidor (server/games/rat_race.py)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading, random, time
from common.messages import MSG_RACE_UPDATE
from config.config import CONFIG_PARAMS

BG = "#061018"
TRACK = "#0f4c5c"
MOUSE_COLOR = "#ffd27a"


class RaceScene(tk.Frame):
    def __init__(self, parent, app):
        """
        parent : contenedor dentro del panel principal
        app    : acceso a net, client_id y show_scene()

        Atributos importantes:
        - local_pos : posiciones locales de TODOS los ratones
        - selected  : cuál ratón escogió este cliente
        - running   : bandera para controlar el hilo local
        """
        super().__init__(parent, bg=BG)
        self.app = app
        self.net = app.net
        self.client_id = app.client_id

        # parámetros desde CONFIG
        self.race_len = CONFIG_PARAMS["RACE_LENGTH"]
        self.num_mice = CONFIG_PARAMS["RACE_NUM_MICE"]

        # Posiciones locales (todas inician en 0)
        self.local_pos = {f"m{i+1}": 0 for i in range(self.num_mice)}

        self.selected = None
        self.running = False

        # Referencias a los objetos gráficos de cada ratón
        self.canvas_objects = {}

        self.build()

    def build(self):
        """Construye toda la interfaz gráfica de la carrera."""
        self.pack(fill="both", expand=True)

        tk.Label(self, text="CARRERA DE RATONES",
                 font=("Arial", 18), fg="#2ef0f0", bg=BG).pack(pady=6)

        # Canvas donde se dibujan pistas y ratones
        self.canvas = tk.Canvas(self, width=self.race_len + 140,
                                height=50*self.num_mice,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        # Dibujar pistas y ratones
        for i in range(self.num_mice):
            y = 20 + i * 50

            # Rectángulo que representa la pista
            self.canvas.create_rectangle(
                10, y - 10,
                self.race_len + 110, y + 20,
                fill=TRACK, outline=""
            )

            # Crear un ratón 🐀 (texto unicode)
            label = f"m{i+1}"
            obj_id = self.canvas.create_text(
                20, y,
                text="🐀", anchor="w",
                fill=MOUSE_COLOR, font=("Arial", 16)
            )

            self.canvas_objects[label] = obj_id

        # Panel de controles
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack()

        tk.Label(ctrl, text="Elige tu ratón:", bg=BG, fg="white").pack()

        # Combobox para elegir ratón
        self.combo = ttk.Combobox(
            ctrl, values=[f"m{i+1}" for i in range(self.num_mice)]
        )
        self.combo.pack(pady=5)

        tk.Button(ctrl, text="Elegir y comenzar",
                  bg="#ff9a2e", command=self.choose).pack(pady=4)

        tk.Button(ctrl, text="Volver",
                  command=lambda: self.app.show_scene("MENU")).pack(pady=4)

    # ---------------------------------------------------------
    # LÓGICA DE SELECCIÓN Y MOVIMIENTO LOCAL
    # ---------------------------------------------------------

    def choose(self):
        """El usuario escoge un ratón y la carrera comienza localmente."""
        choice = self.combo.get()

        if not choice:
            messagebox.showwarning("Error", "Debes elegir un ratón.")
            return

        self.selected = choice
        self.running = True

        # Informar al servidor cuál ratón es nuestro
        self.net.send({
            "type": "RACE_SELECT",
            "client_id": self.client_id,
            "mouse_id": self.selected
        })

        # Iniciar animación local en hilo separado
        threading.Thread(target=self.local_loop, daemon=True).start()

    def local_loop(self):
        """
        Este hilo mueve localmente TODOS los ratones.

        Solo el ratón seleccionado envía su posición al servidor.
        Los demás se mueven como animación "decorativa".
        """
        while self.running:
            for mouse in self.local_pos.keys():

                # Si ya llegó a la meta → no lo movemos más
                if self.local_pos[mouse] >= self.race_len:
                    continue

                # Movimiento aleatorio dentro de los rangos configurados
                step = random.randint(
                    CONFIG_PARAMS["RACE_STEP_MIN"],
                    CONFIG_PARAMS["RACE_STEP_MAX"]
                )

                # Actualizamos posición
                self.local_pos[mouse] += step

                # Clamp para evitar pasarse
                if self.local_pos[mouse] > self.race_len:
                    self.local_pos[mouse] = self.race_len

                # Enviar SOLO nuestro ratón
                if mouse == self.selected:
                    if self.local_pos[mouse] < self.race_len:
                        self.net.send({
                            "type": MSG_RACE_UPDATE,
                            "client_id": self.client_id,
                            "mouse_id": mouse,
                            "pos": self.local_pos[mouse]
                        })

            # Actualizar la GUI
            self.canvas.after(0, self.update_local_gui)

            time.sleep(CONFIG_PARAMS["RACE_INTERVAL"])

    def update_local_gui(self):
        """Mueve visualmente cada ratón según su posición local."""
        for mouse, pos in self.local_pos.items():
            obj = self.canvas_objects[mouse]
            y = self.canvas.coords(obj)[1]  # mantenemos el Y
            self.canvas.coords(obj, 20 + pos, y)

    # ---------------------------------------------------------
    # MANEJO DE MENSAJES DEL SERVIDOR
    # ---------------------------------------------------------

    def handle_server_msg(self, msg):
        """
        El servidor envía solo RACE_FINISH al cliente.
        GAME_STATE lo maneja gui_client.py directamente.
        """
        if msg.get("type") == "RACE_FINISH" and msg.get("client_id") == self.client_id:

            self.running = False  # Detener animación local

            place = msg["your_place"]
            ranking = msg["ranking"]

            # Texto del popup
            texto = "¡GANASTE! 🐀💨" if place == 1 else f"Quedaste #{place}"
            texto += "\n\nRanking final:\n" + "\n".join(ranking)

            messagebox.showinfo("Resultados de la Carrera", texto)
