from dataclasses import dataclass
import socket
from alp import Packet
import select
import queue
import ssl
import sys

@dataclass
class Server:
    host: str = "0.0.0.0"
    port: int = 2137
    
    sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def __post_init__(self):
        self.sock.bind((self.host, self.port))

    def run(self):
        self.sock.listen()

        print(f"Listening for connections on tcp://{self.host}:{self.port}")

        # while True:
            


HOST = "127.0.0.1"
PORT = 2137

context = ssl._create_unverified_context(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("test.crt", "test.key")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def run(s):
    with context.wrap_socket(s, server_side=True) as sock:
        sock.bind((HOST, PORT))
        sock.listen()
        sock.setblocking(0)

        
        potential_readers = [sys.stdin, sock] # Store all sockets
        potential_writers = []
        potential_errs = []
        message_queues = {}

        clients = {}

        while potential_readers:
            ready_to_read, ready_to_write, in_error = select.select(
                potential_readers, potential_writers, potential_errs
            )

            for s in ready_to_read:
                if s is sock:
                    connection, client_address = s.accept() # Accept connection
                    print(f"Connection accepted: {client_address}")
                    connection.setblocking(0)
                    potential_readers.append(connection)
                    message_queues[connection] = queue.Queue()

                    clients[client_address[1]] = connection
                elif s is sys.stdin:
                    message = sys.stdin.readline()
                    message = message.split()

                    message_raw = (" ".join(message[2:]) + "\n").encode("utf-8") 

                    target_port = int(message[1])
                    
                    if target_port in clients:
                        try:
                            clients[target_port].send(message_raw)
                        except Exception as e:
                            print(f"Failed to send message to {target_port}: {e}")
                    else:
                        print(f"No client connected on port {target_port}")

                else:
                    data = s.recv(1024)
                    if data:
                        print(f"Message from {s.getpeername()}: {data}")
                        message_queues[s].put(data)
                        if s not in potential_writers:
                            potential_writers.append(s)
                    else:
                        print(f"{s.getpeername()} disconnected")
                        if s in potential_writers:
                            potential_writers.remove(s)
                        
                        client_port = s.getpeername()[1]

                        if client_port in clients:
                            del clients[client_port]

                        potential_readers.remove(s)
                        s.close()
                        del message_queues[s]
            
            for s in ready_to_write:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    potential_writers.remove(s)
                else:
                    s.send(b"[i] Message received")
            
            for s in potential_errs:
                potential_readers.remove(s)
                if s in potential_writers:
                    potential_writers.remove(s)
                s.close()
                del message_queues[s]


