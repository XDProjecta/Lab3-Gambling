# main_client.py
import tkinter as tk
from client.gui_client import ClientApp
from client.scenes.menu_scene import setup_menu_styles

def main():
    root = tk.Tk()
    setup_menu_styles(root)
    app = ClientApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
