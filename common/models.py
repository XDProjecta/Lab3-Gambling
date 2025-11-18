# common/models.py
import threading
import time
import random
from config.config import CONFIG_PARAMS

STEP_MIN = CONFIG_PARAMS["MOUSE_STEP_MIN"]
STEP_MAX = CONFIG_PARAMS["MOUSE_STEP_MAX"]
UPDATE_INTERVAL = CONFIG_PARAMS["MOUSE_UPDATE_INTERVAL"]

class Mouse(threading.Thread):
    def __init__(self, mouse_id, send_update, start_pos=0):
        super().__init__(daemon=True)
        self.mouse_id = mouse_id
        self.position = start_pos
        self.send_update = send_update

        self._running = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._boost = 0
        self._lock = threading.Lock()

    def run(self):
        self._running = True
        while self._running:
            self._pause_event.wait()

            step = random.randint(STEP_MIN, STEP_MAX)

            with self._lock:
                step += self._boost
                self._boost = 0

            self.position += step

            try:
                self.send_update(self.mouse_id, self.position)
            except:
                pass

            time.sleep(UPDATE_INTERVAL)

    def stop(self):
        self._running = False
        self._pause_event.set()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def boost(self, amount=5):
        with self._lock:
            self._boost += amount
