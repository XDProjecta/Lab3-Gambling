# main_client.py
import tkinter as tk
from client.gui_client import ClientGUI

def main():
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
