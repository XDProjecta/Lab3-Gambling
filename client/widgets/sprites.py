# client/widgets/sprites.py
"""
funciones para dibujar sprites retro en Canvas.
no usa imágenes externas: pq ql pava la vd
"""

def draw_card(canvas, x, y, w=60, h=90, rank="A", suit="♠", fill="#ffffff", outline="#222"):
    # cuerpo carta
    rect = canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline=outline, width=2)
    # esquina superior izquierda
    canvas.create_text(x+10, y+12, text=f"{rank}{suit}", font=("Arial", 10, "bold"), anchor="w")
    # centro
    canvas.create_text(x+w/2, y+h/2, text=suit, font=("Arial", 24))
    return rect

def draw_slot_symbol(canvas, cx, cy, symbol, size=36, neon=None):
    # dibuja símbolo grande
    canvas.create_text(cx, cy, text=symbol, font=("Arial", size), anchor="c")
