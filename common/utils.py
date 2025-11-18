# common/utils.py
import json
from config.config import CONFIG_PARAMS

ENC = CONFIG_PARAMS["ENCODING"]
DELIM = CONFIG_PARAMS["MSG_DELIM"]

def make_msg(obj):
    text = json.dumps(obj) + DELIM
    return text.encode(ENC)

def parse_stream(data):
    try:
        text = data.decode(ENC)
    except:
        return []

    parts = text.split(DELIM)
    msgs = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        try:
            msgs.append(json.loads(p))
        except:
            pass
    return msgs
