from dataclasses import dataclass
import socket
from alp import Packet, PayloadType
import select
import queue
import ssl
import sys
from datetime import datetime, timezone, timedelta
from typing import Any
from tui import TuiMode
import os

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes

@dataclass
class User:
    name: str
    addr: tuple[str, int] # (ip, port)
    accepted: bool
    send_socket: ssl.SSLSocket
    recv_socket: ssl.SSLSocket

    def __str__(self):
        return f'{self.name}@{self.addr[0]}:{self.addr[1]}'
    
    def __key(self):
        return (self.name, self.addr[0], self.addr[1])

    def __hash__(self):
        return hash(self.__key())

@dataclass
class Server:
    sender: str
    control: Any
    public: str = None
    private: str = None
    passwd: str = None
    delete_keys: bool = True
    host: str = "0.0.0.0"
    port: int = 2137
    
    def __post_init__(self):
        if not self.public or not self.private:
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            with open('key.pem', 'wb+') as private_fd:
                private_fd.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.BestAvailableEncryption(self.passwd.encode('utf-8')),
                ))

            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "mazowieckie"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Warszawa"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "secure_messenger"),
            ])

            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.now(timezone.utc)
            ).not_valid_after(
                datetime.now(timezone.utc) + timedelta(days=10)
            ).sign(key, hashes.SHA256())

            with open('cert.pem', 'wb+') as public_fd:
                public_fd.write(cert.public_bytes(serialization.Encoding.PEM))

            self.public = 'cert.pem'
            self.private = 'key.pem'

        self.client_ctx = ssl._create_unverified_context(ssl.PROTOCOL_TLS_CLIENT)
        self.client_ctx.load_cert_chain(self.public, self.private, password=self.passwd)

        self.server_ctx = ssl._create_unverified_context(ssl.PROTOCOL_TLS_SERVER)
        self.server_ctx.load_cert_chain(self.public, self.private, password=self.passwd)

        del self.passwd # discard passwd - it's not used anymore

        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.users: set[User] = set()

        self._pipe_read, self._pipe_write = os.pipe()

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


    def find_by_addr(self, addr: tuple[str, int], ignore_port=False) -> User | None:
        for user in self.users:
            if ignore_port:
                if user.addr[0] == addr[0]:
                    return user
            else:
                if user.addr == addr:
                    return user
        return None
    
    def find_by_recv_socket(self, recv_socket: int) -> User | None:
        for user in self.users:
            if user.recv_socket == recv_socket:
                return user
        return None
    
    def stop(self):
        if self.delete_keys:
            if os.path.exists(self.public):
                os.remove(self.public)
            if os.path.exists(self.private):
                os.remove(self.private)
        os.write(self._pipe_write, b'CLOSE')

    def exit_conversation(self):
        os.write(self._pipe_write, b'EXIT_CONVERSATION')

    def run(self):
        with self.server_ctx.wrap_socket(self.main_socket, server_side=True) as wrapped_socket:
            self.wrapped_socket = wrapped_socket
            wrapped_socket.bind((self.host, self.port))
            wrapped_socket.listen()
            wrapped_socket.setblocking(0)

            self.potential_readers = [wrapped_socket, self._pipe_read] # Store all sockets
            self.potential_writers = []
            self.potential_errs = []

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
 
                        if user := self.find_by_addr(client_address, ignore_port=True):
                            user.recv_socket = connection
                        else:
                            user = User('unknown', client_address, False, None, connection)
                            self.users.add(user)
                    elif s is self._pipe_read:
                        data = os.read(s, 1024)
                        if data == b'CLOSE':
                            exit(0)
                        if data == b'EXIT_CONVERSATION':
                            for u in self.users:
                                if u.send_socket and u.send_socket.fileno() > 0:
                                    u.send_socket.close()
                                if u.recv_socket and u.send_socket.fileno() > 0:
                                    self.potential_readers.remove(u.recv_socket)
                                    u.recv_socket.close()
                            self.users.clear()
                    else:
                        # socket for receiving data
                        data = s.recv(1024)
                        user = self.find_by_recv_socket(s)
                        if not user:
                            continue
                        if data:
                            try:
                                packet = Packet.from_raw(bytearray(data))
                                user.name = packet.sender
                                if packet.port:
                                    user.addr = (user.addr[0], packet.port)
                            except Exception as e:
                                s.send(
                                    Packet.new(
                                        self.sender, 
                                        PayloadType.ERROR, 
                                        f'Unknown packet format\n{e}'
                                    ).to_bytearray()
                                )
                                if s in self.potential_readers:
                                    self.potential_readers.remove(s)
                                if s in self.potential_writers:
                                    self.potential_writers.remove(s)
                                if s in self.potential_errs:
                                    self.potential_errs.remove(s)
                                s.close()
                                continue

                            if packet.dtype in {PayloadType.MSG, PayloadType.WHISPER} and user.accepted:
                                print(f'')
                                print(f"[{packet.sender_time}] {user}{' whispers' if packet.dtype == PayloadType.WHISPER else ''}: {packet.payload}")
                            elif packet.dtype == PayloadType.JOIN:
                                if user in self.users:
                                    continue
                                # prompt user to send ACCEPT/DENY
                                print(f'{user} wants to join the conversation')
                                print(f'You can accept with /accept {user.name}')
                                user.accepted = True
                            elif packet.dtype == PayloadType.ACCEPT:
                                user.accepted = True
                                print(f'{user} accepted the invitation.')
                                self.control.change_mode(TuiMode.Conversation)
                                for u, u_addr in packet.payload.items():
                                    if self.find_by_addr(u_addr):
                                        continue
                                    self.join(u_addr, u)
                        else:
                            print(f'{user} disconnected')
                            new_users = set()
                            for u in self.users:
                                if u.name == user.name and u.addr[0] == user.addr[0] and u.addr[1] == user.addr[1]:
                                    continue
                                new_users.add(u)
                            self.users = new_users

                            if user.send_socket and user.send_socket.fileno() > 0:
                                user.send_socket.close()
                            if user.recv_socket and user.send_socket.fileno() > 0:
                                self.potential_readers.remove(user.recv_socket)
                                user.recv_socket.close()


if __name__ == '__main__':
    Server().run()