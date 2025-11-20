# client/widgets/card_drawer.py
"""
Funciones para 'dibujar' cartas en canvas sin imágenes.
Devuelve strings representativos (ej: 'A♠') o rectángulos con texto.
"""
def card_to_text(card):
    # card: lista o tupla [rank, suit] o ("A","♠")
    try:
        r, s = card
        return f"{r}{s}"
    except Exception:
        return str(card)
