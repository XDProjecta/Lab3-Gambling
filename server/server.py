# server/server.py
"""
Servidor TCP principal.
- Acepta clientes
- Mantiene lista de clientes conectados
- Recibe mensajes y los delega al GameManager
- Envía respuestas o broadcast
"""

import socket
import threading
from config.config import CONFIG_PARAMS
from common.protocol import make_msg, parse_stream
from server.game_manager import GameManager

# Carga de direcciones desde config.json
HOST = CONFIG_PARAMS["SERVER_IP_ADDRESS"]
PORT = CONFIG_PARAMS["SERVER_PORT"]

class Server:
    def __init__(self, host=HOST, port=PORT):
        """
        Constructor del servidor.
        - Inicializa socket TCP
        - Estructuras para manejar clientes
        - Crea instancia del GameManager que coordina los juegos
        """
        self.host = host
        self.port = port

        # Socket TCP del servidor
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Diccionario de clientes conectados:
        # { socket : client_id }
        # a cada cliente se le asigna un socket exclusivo
        self.clients = {}
        self.clients_lock = threading.Lock()
        # Estado del servidor, True si está corriendo, pero por defecto False
        self.running = False

        # GameManager controla rat race, blackjack, slots, etc.
        self.manager = GameManager(self)

    def start(self):
        """
        Inicia el servidor TCP:
        - Bindea IP/PORT
        - Comienza a escuchar conexiones entrantes
        - Lanza hilo que acepta clientes
        """
        # bindear se refiere a asignar una dirección IP y un puerto específico a un socket 
        # para que pueda escuchar conexiones entrantes en esa dirección y puerto.
        self.sock.bind((self.host, self.port))
        # listen pone el socket en modo de escucha para aceptar conexiones entrantes.
        self.sock.listen(CONFIG_PARAMS["SERVER_MAX_CLIENTS"])
        # Estado del servidor ACTIVO
        self.running = True
        # Mensaje en consola cuando el server está listo
        print(f"[SERVER] Escuchando en {self.host}:{self.port}")

        # Hilo que acepta nuevos clientes, daemon se usa para que termine al cerrar el programa
        # accept_loop es el método que maneja la aceptación de conexiones entrantes.
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        """
        Hilo principal que acepta nuevos clientes.
        Cada cliente se atiende en un hilo separado.
        """
        # mientras que el servidor esté corriendo, acepta conexiones entrantes 
        # infinitamente hasta que se detenga el servidor
        while self.running:
            try:
                # accept espera y acepta una nueva conexión entrante
                # devuelve un nuevo socket para comunicarse con el cliente y la dirección del cliente
                # csokk es el socket exclusivo para ese cliente
                csock, addr = self.sock.accept()
                # Mensaje en consola de nueva conexión, addr es una tupla (IP, PORT) que identifica al cliente únicamente por su conexión
                print("[SERVER] Nueva conexión desde", addr)

                # Crea un hilo exclusivo para leer mensajes del cliente
                threading.Thread(target=self._handle_client, args=(csock,), daemon=True).start()

            except Exception as e:
                print("[SERVER] Error en accept:", e)

    def _handle_client(self, csock):
        """
        Maneja un cliente:
        - Lee mensajes continuamente
        - Parsea mensajes según nuestro protocolo
        - Si es REGISTER entonces registra el cliente
        - Si no entonces delega al GameManager
        """
        # Variables locales, donde addr es la dirección del cliente, client_id es su ID único  
        # y buf es el buffer de datos recibidos (inicialmente vacío)
        # lo que hace buf es almacenar datos parciales recibidos del cliente, para luego procesarlos cuando se complete un mensaje
        # sirve para manejar la fragmentación TCP, que ocurre cuando los datos enviados por el cliente llegan en partes
        # la fragmentación TCP es un fenómeno donde los datos enviados a través de una conexión TCP pueden llegar en partes o fragmentos
        addr = None
        client_id = None
        buf = b""  # buffer para fragmentación TCP

        try:
            # Obtener dirección del cliente por medio del socket del cliente
            addr = csock.getpeername()
            # mientras el servidor esté corriendo, lee datos del cliente
            while True:
                # Lee datos del socket del cliente (4096 bytes como máximo) por medio del socket del cliente
                data = csock.recv(4096)
                # si no hay datos, el cliente se desconectó
                if not data:
                    break  # cliente desconectado
                    # Añadir datos recibidos al buffer
                buf += data

                # parse_stream devuelve una lista de mensajes completos 
                msgs = parse_stream(buf)
                # aquí lo que hacemos es limpiar el buffer solo si parse_stream dio mensajes
                buf = b""  # limpiar buffer

                # para cada mensaje completo recibido
                for msg in msgs:
                    # Mensaje en consola
                    print(f"[SERVER] Mensaje recibido de {addr}: {msg}")
                    # si es un mensaje de registro, entonces registramos al cliente
                    # Registro inicial
                    if msg.get("type") == "REGISTER":
                        client_id = msg.get("client_id")

                        # Guardamos el cliente en el diccionario
                        # lock para evitar condiciones de carrera, ya que múltiples hilos pueden escribir al dict
                        # es decir, varios clientes pueden conectarse al mismo tiempo
                        # sucede por ejemplo, que dos clientes intentan registrarse simultáneamente
                        # esto puede llevar a que ambos hilos accedan y modifiquen el diccionario de clientes al mismo tiempo
                        # y hacer que se pierdan datos o se corrompa la estructura del diccionario
                        with self.clients_lock:
                            # asignar el client_id al socket del cliente en el diccionario de clientes
                            # clients es un diccionario que mapea sockets de clientes a sus IDs únicos
                            # esto permite al servidor identificar y comunicarse con cada cliente de manera individual
                            # aquí estamos registrando un nuevo cliente en el servidor
                            # el socket del cliente csock se usa como clave y el client_id como valor
                            # de esta manera, el servidor puede rastrear qué cliente está asociado con qué socket
                            self.clients[csock] = client_id

                        # Respuesta confirmando registro
                        # enviamos un mensaje al cliente confirmando que se ha registrado correctamente
                        # usamos make_msg para serializar el mensaje, donde
                        #  el mensaje contiene el tipo "REGISTERED" y el client_id del cliente
                        # esto le indica al cliente que su registro fue exitoso
                        # enviamos entonces el mensaje al socket del cliente
                        csock.sendall(make_msg({
                            "type":"REGISTERED",
                            "client_id": client_id
                        }))

                        # Finalmente,
                        # notificamos al GameManager que un nuevo cliente se ha registrado
                        # esto permite al GameManager inicializar cualquier dato necesario para ese cliente
                        # llamamos al método on_client_register del GameManager para manejar la lógica de registro
                        self.manager.on_client_register(client_id, csock)
                        continue

                    # Cualquier otro mensaje va al GameManager
                    # delegamos el procesamiento del mensaje al GameManager por medio del método process_message
                    self.manager.process_message(msg, csock)

        except Exception as e:
            print(f"[SERVER] Error manejando cliente {addr}: {e}")

        finally:
            print(f"[SERVER] Cliente desconectado {addr}")

            # Sacamos al cliente del dict de clientes conectados cuando se desconecta
            with self.clients_lock:
                self.clients.pop(csock, None)

            # Notificamos al GameManager de la desconexión
            try:
                self.manager.on_client_disconnect(client_id, csock)
            except:
                pass

            # Cerramos socket del cliente desconectado
            try:
                csock.close()
            except:
                pass

    def send(self, csock, obj):
        """
        Envia un mensaje a un cliente.
        """
        try:
            # envía el mensaje serializado al socket del cliente por medio del socket del cliente y el objeto a enviar
            # make_msg serializa el objeto a formato JSON y añade el delimitador, que es necesario para que el cliente pueda parsearlo correctamente
            # el objeto obj es un diccionario que representa el mensaje a enviar
            csock.sendall(make_msg(obj))
        except:
            pass  # Si falla, se maneja en otro lado

    def broadcast(self, obj):
        """
        Envía un mensaje a TODOS los clientes conectados.
        """
        # para cada socket de cliente en el diccionario de clientes conectados
        # usamos un lock para evitar condiciones de carrera al iterar sobre el diccionario
        # las condiciones de carrera son problemas que ocurren cuando múltiples hilos acceden 
        # y modifican datos compartidos al mismo tiempo
        # esto puede llevar a resultados inesperados o inconsistentes, por lo quue 
        # usamos un lock para asegurar que solo un hilo pueda acceder al diccionario a la vez
        with self.clients_lock:
            # iteramos sobre una copia de las claves del diccionario de clientes
            # esto es para evitar errores si el diccionario cambia mientras iteramos
            for csock in list(self.clients.keys()):
                try:
                    # enviamos el mensaje serializado a cada socket de cliente
                    csock.sendall(make_msg(obj))
                except:
                    pass  # se limpiará en el hilo del cliente

    def stop(self):
        """
        Apaga el servidor completamente.
        """
        # Cambiar estado para que los hilos terminen
        self.running = False

        try:
            # Cerrar socket del servidor
            self.sock.close()
        except:
            pass

        # Cerramos los clientes
        # usamos un lock para evitar condiciones de carrera al iterar sobre el diccionario
        # nuevamente, iteramos sobre una copia de las claves del diccionario para evitar errores
        with self.clients_lock:
            for csock in list(self.clients.keys()):
                try:
                    csock.close()
                except:
                    pass

        print("[SERVER] Servidor detenido.")
