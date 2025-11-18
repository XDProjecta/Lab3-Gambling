# main_server.py
import tkinter as tk
from server.gui_server import ServerGUI

def main():
    root = tk.Tk()
    gui = ServerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
