# client/gui_client.py
import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import queue
from config.config import CONFIG_PARAMS
from common.models import Mouse
from client.client import RaceClient

RACE_LEN = CONFIG_PARAMS["RACE_LENGTH"]

class ClientGUI:
    def __init__(self, root, client_id=None, num_mice=None):
        self.root = root
        self.client_id = client_id or f"client-{str(uuid.uuid4())[:6]}"
        self.num_mice = num_mice or CONFIG_PARAMS["DEFAULT_NUM_MICE"]
        self.client = RaceClient(self.client_id, on_positions_update=self.on_positions_update)
        self.mice = {}
        self.mouse_labels = {}
        self.queue = queue.Queue()
        self._build_ui()
        self.root.after(100, self._process_queue)

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text=f"Cliente: {self.client_id}", font=("Arial", 12)).pack(side="left")
        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right")
        self.conn_btn = ttk.Button(btn_frame, text="Conectar", command=self.connect)
        self.conn_btn.pack(side="left", padx=4)
        self.start_btn = ttk.Button(btn_frame, text="Start Race", command=self.start_race, state="disabled")
        self.start_btn.pack(side="left", padx=4)
        self.pause_btn = ttk.Button(btn_frame, text="Pause Race", command=self.pause_race, state="disabled")
        self.pause_btn.pack(side="left", padx=4)
        self.canvas = tk.Canvas(self.root, width=RACE_LEN+100, height=40 * self.num_mice + 40, bg="white")
        self.canvas.pack(padx=8, pady=8)
        ctrl = ttk.Frame(self.root, padding=6)
        ctrl.pack(fill="x")
        ttk.Label(ctrl, text="Seleccionar ratón:").pack(side="left")
        self.sel_var = tk.StringVar()
        self.sel_combo = ttk.Combobox(ctrl, textvariable=self.sel_var, state="readonly")
        self.sel_combo.pack(side="left", padx=6)
        self.boost_btn = ttk.Button(ctrl, text="Boost (+10)", command=self.boost_selected, state="disabled")
        self.boost_btn.pack(side="left", padx=6)
        self.status = ttk.Label(self.root, text="Desconectado")
        self.status.pack(fill="x")
        for i in range(self.num_mice):
            mid = f"m{ i + 1 }"
            y = 20 + i * 40
            label = tk.Label(self.canvas, text="🐀", font=("Arial", 18))
            label.place(x=10, y=y)
            self.mouse_labels[mid] = label
        self.sel_combo['values'] = list(self.mouse_labels.keys())

    def connect(self):
        try:
            self.client.connect()
            self.status.config(text="Conectado al servidor")
            self.conn_btn.config(state="disabled")
            self.start_btn.config(state="normal")
            self.boost_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {e}")

    def start_race(self):
        for mid in list(self.mouse_labels.keys()):
            if mid in self.mice:
                self.mice[mid].resume()
            else:
                def send_update_closure(mouse_id, pos, mid=mid):
                    self.queue.put(("local_update", mid, pos))
                    try:
                        self.client.send_mouse_update(mid, pos)
                    except:
                        pass
                m = Mouse(mid, send_update=send_update_closure, start_pos=0)
                self.mice[mid] = m
                m.start()
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.status.config(text="Carrera en curso (local)")

    def pause_race(self):
        for m in self.mice.values():
            m.pause()
        self.pause_btn.config(state="disabled")
        self.start_btn.config(state="normal")
        self.status.config(text="Pausado")

    def boost_selected(self):
        sel = self.sel_var.get()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona un ratón para boost.")
            return
        m = self.mice.get(sel)
        if m:
            m.boost(10)
            self.queue.put(("boost", sel))

    def on_positions_update(self, positions):
        self.queue.put(("positions", positions))

    def _process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "positions":
                    positions = item[1]
                    our = positions.get(self.client.client_id, {})
                    for mid, pos in our.items():
                        self._move_label(mid, pos)
                elif item[0] == "local_update":
                    mid, pos = item[1], item[2]
                    self._move_label(mid, pos)
                elif item[0] == "boost":
                    mid = item[1]
                    lbl = self.mouse_labels.get(mid)
                    if lbl:
                        lbl.config(font=("Arial", 22))
                        self.root.after(150, lambda l=lbl: l.config(font=("Arial", 18)))
        except Exception:
            pass
        finally:
            self.root.after(100, self._process_queue)

    def _move_label(self, mid, pos):
        lbl = self.mouse_labels.get(mid)
        if not lbl:
            return
        x = min(pos, RACE_LEN)
        y = lbl.winfo_y()
        lbl.place(x=10 + x, y=y)
