# client/client.py
"""
NetworkClient
-------------
Este módulo implementa el cliente TCP que se comunica con el servidor.

FUNCIONES PRINCIPALES:
- Conectarse al servidor
- Enviar mensajes usando el protocolo make_msg()
- Recibir mensajes en un hilo dedicado
- Llamar un callback on_message(msg) cuando llega un mensaje del server
- Manejar desconexiones sin crashear la GUI

Este cliente NO interpreta la lógica del juego.
Solo transporta mensajes → la GUI los interpreta.
"""

import socket
import threading
import time
from common.protocol import make_msg, parse_stream
from config.config import CONFIG_PARAMS

# Dirección y puerto del servidor desde config.yaml
SERVER_IP = CONFIG_PARAMS["SERVER_IP_ADDRESS"]
SERVER_PORT = CONFIG_PARAMS["SERVER_PORT"]


class NetworkClient:
    def __init__(self, client_id, on_message=None):
        """
        Inicializa el cliente de red.

        Parámetros:
        - client_id: nombre único del cliente.  
                      Lo envía al servidor después de conectarse.
        - on_message: función callback llamada cada vez que llega un mensaje
                      decodificado desde el servidor.

        Atributos:
        - connected: indica si la conexión está activa.
        - sock: socket TCP.
        - _recv_thread: hilo encargado de recibir mensajes.
        - _lock: asegura que send() no sea interrumpido.
        """
        self.client_id = client_id
        self.on_message = on_message

        self.sock = None
        self.connected = False
        self._lock = threading.Lock()
        self._recv_thread = None

        # Última vez que recibimos datos (puede servir para timeout)
        self._last_recv = 0.0


    # ----------------------------------------------------------------------
    # CONEXIÓN AL SERVIDOR
    # ----------------------------------------------------------------------

    def connect(self, host=None, port=None, timeout=3):
        """
        Intentar conectarse al servidor.
        Levanta excepción si falla para que la GUI pueda mostrar errores.

        - host / port: permite sobrescribir los valores de config.
        - timeout: corta el intento si se demora demasiado.
        """
        host = host or SERVER_IP
        port = port or SERVER_PORT

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)

        try:
            self.sock.connect((host, port))
        except Exception as e:
            # No se pudo conectar: dejamos limpio el estado
            self.connected = False
            try:
                self.sock.close()
            except:
                pass
            raise e  # propagamos el error a la GUI

        # Conectado exitosamente
        self.sock.settimeout(None)
        self.connected = True

        # Enviar mensaje de registro
        self.send({"type": "REGISTER", "client_id": self.client_id})

        # Crear hilo de recepción
        self._recv_thread = threading.Thread(
            target=self._recv_loop, daemon=True
        )
        self._recv_thread.start()


    # ----------------------------------------------------------------------
    # ENVÍO DE MENSAJES
    # ----------------------------------------------------------------------

    def send(self, obj):
        """
        Envía un mensaje al servidor.

        - Serializa usando make_msg()
        - Usa lock para evitar que dos hilos escriban al socket simultáneamente
        - Si hay error, cierra la conexión silenciosamente
        """
        if not self.connected or not self.sock:
            return

        try:
            with self._lock:
                self.sock.sendall(make_msg(obj))
        except Exception:
            # El servidor probablemente murió → cerramos sin crashear
            self.close()


    # ----------------------------------------------------------------------
    # RECEPCIÓN DE MENSAJES
    # ----------------------------------------------------------------------

    def _recv_loop(self):
        """
        Hilo encargado de recibir bytes desde el servidor.

        Este hilo:
        - Lee el socket constantemente
        - Decodifica los mensajes usando parse_stream()
        - Llama on_message(msg) en la GUI para procesar la lógica
        """
        buf = b""

        try:
            while self.connected:
                data = self.sock.recv(4096)

                if not data:  # desconexión limpia
                    break

                self._last_recv = time.time()
                buf += data

                # Obtener lista de mensajes completos
                msgs = parse_stream(buf)
                buf = b""  # limpiar buffer solo si parse_stream dio mensajes

                for m in msgs:
                    if self.on_message:
                        try:
                            self.on_message(m)
                        except Exception:
                            # errores en la GUI no deben detener la red
                            pass

        except Exception:
            # errores típicos: servidor caído, conexión perdida
            pass

        finally:
            # siempre cerramos correctamente
            self.close()


    # ----------------------------------------------------------------------
    # CIERRE / ESTADO
    # ----------------------------------------------------------------------

    def close(self):
        """
        Cierra el socket y marca el cliente como desconectado.
        No lanza excepciones hacia la GUI.
        """
        self.connected = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass

    def is_connected(self):
        """Devuelve True si la conexión sigue activa."""
        return bool(self.connected)
