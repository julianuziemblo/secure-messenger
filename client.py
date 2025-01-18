from alp import Packet, PayloadType
from datetime import datetime

import socket
import ssl

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

context = ssl._create_unverified_context(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations("test.crt")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

with context.wrap_socket(s) as sock:
    sock.connect((HOST, PORT))
    sock.send(b"manialuka")
    data = sock.recv(1024)
    
    print(data.decode())


print(f"Received {data}")
