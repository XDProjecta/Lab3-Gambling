# server/gui_server.py
import tkinter as tk
from tkinter import ttk
from server.server import RaceServer

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Servidor - Carrera de Ratones")
        self.server = RaceServer()
        self.build_ui()
        self.root.after(200, self.refresh_positions)

    def build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Servidor - Carrera de Ratones", font=("Arial", 14)).pack(side="left")
        btnbox = ttk.Frame(top)
        btnbox.pack(side="right")
        self.start_btn = ttk.Button(btnbox, text="Iniciar", command=self.start)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(btnbox, text="Detener", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        cols = ("cliente", "raton", "pos")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", height=15)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

    def start(self):
        self.server.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop(self):
        self.server.stop()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        for item in self.tree.get_children():
            self.tree.delete(item)

    def refresh_positions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            with self.server.positions_lock:
                snapshot = {k: v.copy() for k, v in self.server.positions.items()}
        except:
            snapshot = {}
        for cid, mice in snapshot.items():
            for mid, pos in mice.items():
                self.tree.insert("", "end", values=(cid, mid, pos))
        self.root.after(200, self.refresh_positions)

if __name__ == "__main__":
    root = tk.Tk()
    ServerGUI(root)
    root.mainloop()
