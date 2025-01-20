from dataclasses import dataclass
import socket
from alp import Packet, PayloadType
import select
import queue
import ssl
import sys
from datetime import datetime
from typing import Any
from tui import TuiMode
import os

@dataclass
class User:
    name: str
    addr: tuple[str, int] # (ip, port)
    accepted: bool
    send_socket: int # socket
    recv_socket: int # socket

    def __str__(self):
        return f'{self.name}@{self.addr[0]}:{self.addr[1]}'
    
    def __key(self):
        return (self.name, self.addr[0], self.addr[1], self.send_socket, self.recv_socket)

    def __hash__(self):
        return hash(self.__key())

@dataclass
class Server:
    sender: str
    control: Any
    host: str = "0.0.0.0"
    port: int = 2137
    
    def __post_init__(self):
        self.client_ctx = ssl._create_unverified_context(ssl.PROTOCOL_TLS_CLIENT)
        self.client_ctx.load_cert_chain("test.crt", "test.key")

        self.server_ctx = ssl._create_unverified_context(ssl.PROTOCOL_TLS_SERVER)
        self.server_ctx.load_cert_chain("test.crt", "test.key")

        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.users = set() # set(User)

        self._exit_read, self._exit_write = os.pipe()

    def send(self, packet: Packet, user: User):
        # 1. find the socket
        if not user.send_socket:
            unsecure_send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket = self.client_ctx.wrap_socket(unsecure_send_socket)
            user.send_socket = send_socket
            user.send_socket.connect(user.addr)
        user.send_socket.send(packet.to_bytearray())

    def sendall(self, packet: Packet):
        for user in self.users:
            if user.send_socket:
                user.send_socket.send(packet.to_bytearray())
    
    def join(self, addr: tuple[str, int], username=None):
        packet = Packet.new(
            self.sender,
            PayloadType.JOIN,
            None,
            port=self.port
        )
        try:
            unsecure_send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            send_socket = self.client_ctx.wrap_socket(unsecure_send_socket)

            send_socket.connect(addr)

            send_socket.send(packet.to_bytearray())

            self.users.add(User('unknown' if username is None else username, addr, True, send_socket, None))
        except Exception as e:
            print(f'Couldn\'t connect to requested address: {e}')


    def find_by_addr(self, addr: tuple[str, int]) -> User | None:
        for user in self.users:
            if user.addr == addr:
                return user
        return None
    
    def find_by_recv_socket(self, recv_socket: int) -> User | None:
        for user in self.users:
            if user.recv_socket == recv_socket:
                return user
        return None
    
    def stop(self):
        os.write(self._exit_write, b'CLOSE')

    def run(self):
        with self.server_ctx.wrap_socket(self.main_socket, server_side=True) as wrapped_socket:
            self.wrapped_socket = wrapped_socket
            wrapped_socket.bind((self.host, self.port))
            wrapped_socket.listen()
            wrapped_socket.setblocking(0)

            self.potential_readers = [wrapped_socket, self._exit_read] # Store all sockets
            self.potential_writers = []
            self.potential_errs = []
            self.message_queues = {}

            while self.potential_readers:
                ready_to_read, ready_to_write, in_error = select.select(
                    self.potential_readers, 
                    self.potential_writers, 
                    self.potential_errs
                )

                for s in ready_to_read:
                    if s is wrapped_socket:
                        # socket for accepting connections
                        connection, client_address = s.accept() # Accept connection
                        print(f"Connection accepted: {client_address}")
                        connection.setblocking(0)
                        self.potential_readers.append(connection)
                        self.message_queues[connection] = queue.Queue()   

                        if user := self.find_by_addr(client_address):
                            user.recv_socket = connection
                        else:
                            user = User('unknown', client_address, False, None, connection)
                            self.users.add(user)
                    elif s is self._exit_read:
                        exit(0)
                    else:
                        # socket for receiving data
                        data = s.recv(1024)
                        if data == b'\x00' * 32 + b'CLOSE':
                            exit(0)
                        user = self.find_by_recv_socket(s)
                        if data:
                            try:
                                packet = Packet.from_raw(bytearray(data))
                                user.name = packet.sender
                                if packet.port:
                                    user.addr = (user.addr[0], packet.port)
                                    # print(f'DEBUG: setting port={packet.port} for {user}')
                            except Exception as e:
                                # print(f'DEBUG: got bad packet: {data}, reason: {e}')
                                s.send(
                                    Packet.new(
                                        self.sender, 
                                        PayloadType.ERROR, 
                                        'Unknown packet format'
                                    ).to_bytearray()
                                )
                                del self.users[s]
                                if s in self.potential_readers:
                                    self.potential_readers.remove(s)
                                if s in self.potential_writers:
                                    self.potential_writers.remove(s)
                                if s in self.potential_errs:
                                    self.potential_errs.remove(s)
                                s.close()
                                continue

                            if packet.dtype in {PayloadType.MSG, PayloadType.WHISPER} and user.accepted:
                                print(f"{user}{' whispers' if packet.payload == PayloadType.WHISPER else ''}: {packet.payload}")
                            elif packet.dtype == PayloadType.JOIN:
                                # prompt user to send ACCEPT/DENY
                                print(f'{user} wants to join the conversation')
                                print(f'You can accept with /accept {user.name}')
                                user.accepted = True
                            elif packet.dtype == PayloadType.ACCEPT:
                                user.accepted = True
                                print(f'{user} accepted the invitation.')
                                self.control.change_mode(TuiMode.Conversation)
                                for u, u_addr in packet.payload.items():
                                    self.join(u_addr, u)
                        else:
                            # find user by socket
                            print(f"{user} disconnected")
                            if s in self.potential_writers:
                                self.potential_writers.remove(s)

                            self.potential_readers.remove(s)
                            s.close()
                            del self.message_queues[s]
                
                for s in ready_to_write:
                    try:
                        next_msg = self.message_queues[s].get_nowait()
                    except queue.Empty:
                        self.potential_writers.remove(s)
                    else:
                        s.send(b"[i] Message received")
                
                for s in self.potential_errs:
                    self.potential_readers.remove(s)
                    if s in self.potential_writers:
                        self.potential_writers.remove(s)
                    s.close()
                    del self.message_queues[s]

        # while True:

if __name__ == '__main__':
    Server().run()