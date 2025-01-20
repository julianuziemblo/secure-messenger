from typing import Any
from alp import Packet, PayloadType
from server import Server, User


class AppLogic:
    def __init__(self, control: Any, username: str, port=2137):
        self.running = False
        self.control = control
        self.server = Server(username, control, port=port)

    def run(self):
        self.running = True
        self.server.run()

    def send(self, packet: Packet, user: User):
        self.server.send(packet, user)

    def sendall(self, packet: Packet):
        self.server.sendall(packet)

    def join(self, ip: str, port: int):
        self.server.join((ip, port))

    def find_by_username(self, username: str):
        for u in self.server.users:
            if u.name == username:
                return u
        return None
    
    def find_by_ip(self, ip: str):
        for u in self.server.users:
            if u.ip[0] == ip:
                return u
        return None

    def stop(self):
        self.server.stop()