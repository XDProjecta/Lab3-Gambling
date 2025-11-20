# client/widgets/card_drawer.py
"""
Funciones para 'dibujar' cartas en canvas sin imágenes.
Devuelve strings representativos (ej: 'A♠') o rectángulos con texto.
"""
def card_to_text(card):
    # card: ["A","♠"] or ["10","♥"]
    try:
        r, s = card
        return f"{r}{s}"
    except:
        return str(card)
