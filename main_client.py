# main_client.py
import tkinter as tk
from client.gui_client import ClientApp

def main():
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
