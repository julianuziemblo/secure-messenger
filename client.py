from alp import Packet, PayloadType
from datetime import datetime

import socket

packet = Packet(
    'User1',
    datetime(1979, 9, 6, 0, 51, 36),
    bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
    0x5,
    PayloadType.MSG,
    'hello'
)

raw_packet = packet.to_bytearray()

HOST = "127.0.0.1"
PORT = 2137

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connecT((HOST, PORT))

    sock.sendall(raw_packet)

    data = sock.recv(1024)

print(f"Received {data}")
