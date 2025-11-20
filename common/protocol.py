# common/protocol.py
import json
from config.config import CONFIG_PARAMS

ENC = CONFIG_PARAMS["ENCODING"]
DELIM = CONFIG_PARAMS["MSG_DELIM"]

def make_msg(obj: dict) -> bytes:
    """Serializa dict a JSON y añade delimitador."""
    return (json.dumps(obj) + DELIM).encode(ENC)

def parse_stream(data: bytes):
    """
    Convierte buffer en lista de mensajes dict.
    Maneja múltiples mensajes concatenados por DELIM.
    """
    try:
        text = data.decode(ENC)
    except Exception:
        return []
    parts = text.split(DELIM)
    msgs = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        try:
            msgs.append(json.loads(p))
        except Exception:
            # ignorar mensaje mal formado
            continue
    return msgs
