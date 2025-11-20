# config/config.py
# Parámetros globales del proyecto

CONFIG_PARAMS = {
    # Para arrancar el servidor: usa "0.0.0.0" para escuchar todas las interfaces
    # Para los clientes: reemplaza por la IP del servidor (ej. "192.168.0.15") cuando pruebes en LAN
    "SERVER_IP_ADDRESS": "10.20.24.66",
    "SERVER_PORT": 5000,
    "SERVER_MAX_CLIENTS": 50,

    # Carrera de ratones
    "RACE_NUM_MICE": 3,
    "RACE_LENGTH": 500,
    "RACE_STEP_MIN": 1,
    "RACE_STEP_MAX": 6,
    "RACE_INTERVAL": 0.12,

    # Blackjack
    "BLACKJACK_MIN_PLAYERS": 1,  # permite 1+ jugadores (dealer siempre en servidor)

    # Slots
    "SLOTS_REELS": 3,
    "SLOTS_SYMBOLS": ["🍒", "🍋", "🔔", "⭐", "7"],

    # Comunicación
    "ENCODING": "utf-8",
    "MSG_DELIM": "\n",
}
