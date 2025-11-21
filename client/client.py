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

# Dirección y puerto del servidor desde config
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
        # Creamos el socket y aplicamos timeout para la conexión inicial
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)

        try:
            # si no se puede conectar, se lanza excepción
            self.sock.connect((host, port))
        except Exception as e:
            # No se pudo conectar: dejamos limpio el estado
            self.connected = False
            try:
                # cerramos el socket si fue creado
                self.sock.close()
            except:
                pass
            raise e  # propagamos el error a la GUI

        # Conectado exitosamente
        # Quitamos el timeout para operaciones normales
        self.sock.settimeout(None)
        self.connected = True

        # Enviar mensaje de registro
        self.send({"type": "REGISTER", "client_id": self.client_id})

        # Crear hilo de recepción
        # este hilo llama on_message() cuando llegan mensajes
        # y se ejecuta en segundo plano para no bloquear la GUI
        self._recv_thread = threading.Thread(
            target=self._recv_loop, daemon=True
        )
        # iniciar el hilo de recepción de mensajes desde el servidor 
        self._recv_thread.start()


    # ----------------------------------------------------------------------
    # ENVÍO DE MENSAJES
    # ----------------------------------------------------------------------

    def send(self, obj):
        """
        Envía un mensaje al servidor.

        - Serializa usando make_msg()
        - Usa lock para evitar que dos hilos escriban al socket simultáneamente
        - Si hay error, cierra la conexión sin decir nada a la GUI
        """
        # Si no estamos conectados, no hacemos nada
        if not self.connected or not self.sock:
            return

        try:
            # enviamos el mensaje serializado al servidor
            # usamos un lock para evitar condiciones de carrera al enviar datos
            with self._lock:
                # enviar todos los bytes del mensaje al socket
                self.sock.sendall(make_msg(obj))
        except Exception:
            # El servidor probablemente murió :v, entonces cerramos sin crashear
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
        # limpiamos el buffer de recepción para almacenar datos entrantes cada vez que llegan
        buf = b""

        try:
            # mientras estemos conectados, leemos datos del socket
            while self.connected:
                # leer hasta 4096 bytes del socket 
                data = self.sock.recv(4096)
                # si no hay datos, el servidor cerró la conexión
                if not data:  # desconexión limpia
                    break
                # actualizar el tiempo del último mensaje recibido
                self._last_recv = time.time()
                # agregar los datos recibidos al buffer
                buf += data

                # Obtenemos lista de mensajes completos por medio de parse_stream 
                msgs = parse_stream(buf)
                buf = b""  # limpiamos buffer solo si parse_stream dio mensajes
                # para cada mensaje completo recibido en el buffer, llamamos al callback on_message
                for m in msgs:
                    if self.on_message:
                        try:
                            self.on_message(m)
                        except Exception:
                            # si on_message falla, no crasheamos el hilo
                            pass

        except Exception:
            # ponemos esto para errores típicos: servidor caído, conexión perdida, etc etc etc.
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
        No lanza excepciones hacia la GUI del cliente.
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
