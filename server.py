from dataclasses import dataclass
import socket
from alp import Packet
import select
import queue
import sys
import termios
import tty

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


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((HOST, PORT))
    sock.listen()
    sock.setblocking(0)
    # conn, addr = sock.accept()

    potential_readers = [sock, sys.stdin]
    potential_writers = []
    potential_errs = []
    message_queues = {}

    old_terminal_settings = termios.tcgetattr(sys.stdin.fileno())
    tty.setcbreak(sys.stdin.fileno())

    while potential_readers:
        ready_to_read, ready_to_write, in_error = select.select(
            potential_readers, potential_writers, potential_errs
        )
        

        buffer = ""

        for s in ready_to_read:
            if s is sock:
                connection, client_address = s.accept()
                print(f"Connection accepted: {client_address}")
                connection.setblocking(0)
                potential_readers.append(connection)
                message_queues[connection] = queue.Queue()
            
            else:
                data = s.recv(1024)
                if data:
                    print(f"Message from {s.getpeername()}: {data}")
                    message_queues[s].put(data)
                    if s not in potential_writers:
                        potential_writers.append(s)
                else:
                    if s in potential_writers:
                        potential_writers.remove(s)
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





    # with conn:
    #     print(f"Connected by {addr}")
    #     while True:
    #         data = conn.recv(1024)
    #         print(data)
    #         if not data:
    #             break
    #         print(data)
    #         conn.sendall(data)