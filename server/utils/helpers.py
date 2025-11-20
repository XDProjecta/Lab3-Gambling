# server/utils/helpers.py
# Funciones utilitarias del servidor

import random

def shuffle_deck():
    ranks = list(range(2,11)) + ["J","Q","K","A"]
    suits = ["♠","♥","♦","♣"]
    deck = []
    for s in suits:
        for r in ranks:
            deck.append((str(r), s))
    random.shuffle(deck)
    return deck

def card_value(card):
    r, _ = card
    if r in ("J","Q","K"):
        return 10
    if r == "A":
        return 11
    return int(r)

def hand_value(hand):
    total = sum(card_value(c) for c in hand)
    aces = sum(1 for c in hand if c[0] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total
