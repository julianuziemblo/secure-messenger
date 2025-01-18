from typing import Any
from alp import Packet, PayloadType


class AppLogic:
    def __init__(self, control: Any, username: str):
        self.running = False
        self.users = {}
        self.username = username

    def run(self):
        self.running = True
        while self.running:
            packet, sender_ip = self.receive_packet()
            match packet.dtype:
                case PayloadType.JOIN: 
                    print(f'New connection request from {packet.sender}@{sender_ip}')
                    print('Use `/accept` to accept')
                case PayloadType.ACCEPT:
                    # TODO: this should only work if the user has sent a JOIN request
                    print(f'{packet.sented}@{sender_ip} accepted your connection request')
                    self.users = packet.payload
                case PayloadType.DENY:
                    # TODO: this should only work if the user has sent a JOIN request
                    print(f'{packet.sented}@{sender_ip} denied your connection request')
                case PayloadType.MSG:
                    print(f'{packet.sender}@{sender_ip}: {packet.payload}')
                case PayloadType.WHISPER:
                    print(f'{packet.sender}@{sender_ip} whispers to you: {packet.payload}')
                case PayloadType.ERROR:
                    print(f'An error occured: {packet.payload}')
                    # TODO: Display only in verbose mode
                case PayloadType.RUA:
                    self.send_packet(Packet())
                case PayloadType.IAA:
                    ... # TODO: check last RUA time for this user. If it's bigger than some TIMEOUT - remove him.
                case PayloadType.NEW_USR:
                    for (name, ip) in packet.payload.values():
                        self.users[name] = ip
                case PayloadType.DEL_USR:
                    users = {}
                    for (name, ip) in packet.payload.values():
                        if name not in users.keys():
                            users[name] = ip
                    self.users = users


    def stop(self):
        self.running = False

    def receive_packet(self, timeout=0) -> tuple[Packet, Any]: # TODO: Any - placeholder for the sender address
        ... # TODO
    
    def send_packet(self, packet: Packet, receiver, timeout=0):
        ... # TODO