from alp import Packet, PayloadType
from datetime import datetime
import time

import socket
import ssl

packet = Packet.new(
    'User1',
    PayloadType.JOIN,
    None
)

raw_packet = packet.to_bytearray()

HOST = "127.0.0.1"
PORT = 2137

context = ssl._create_unverified_context(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations("test.crt")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

with context.wrap_socket(s) as sock:
    sock.connect((HOST, PORT))
    sock.send(raw_packet)
    data = sock.recv(1024)
    
    print(Packet.from_raw(bytearray(data)))
    time.sleep(5)


print(f"Received {data}")
