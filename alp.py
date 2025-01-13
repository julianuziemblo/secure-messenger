from dataclasses import dataclass
from datetime import datetime
from typing import Union, Self


PACKET_TYPE: dict[int, str] = {
    0x1: 'JOIN',
    0x2: 'ACCEPT',
    0x3: 'DENY',
    0x4: 'MSG',
    0x5: 'WHISPER',
    0x6: 'ERROR',
    0x7: 'RUA',
    0x8: 'IAA',
    0x9: 'NEW_USR',
    0xA: 'DEL_USR'
}


@dataclass
class Packet:
    sender: str
    sender_time: datetime
    rsvd: bytearray
    dlen: int
    dtype: int
    payload: Union[None, dict[str, int], str]

    def to_bytearray(self) -> bytearray:
        sender = bytearray(b''.join([bytes(self.sender[i], encoding='ascii') if i < len(self.sender) else b'\x00' for i in range(32)]))
        sender_time = Packet._serialize_int(int(self.sender_time.timestamp()), 4)
        dlen = Packet._serialize_int(self.dlen, 8)
        dtype = Packet._serialize_int(self.dtype, 4)
        payload = self._serialize_payload()
        return sender + sender_time + self.rsvd + dlen + dtype + payload

    @classmethod
    def from_raw(cls, b: bytearray) -> Self:
        sender = Packet._parse_sender(b[0:32:])
        sender_time = Packet._parse_sender_time(b[32:36:])
        rsvd = b[36:52:]
        dlen = Packet._parse_number(b[52:60:])
        dtype = Packet._parse_number(b[60:64:])
        payload = Packet._parse_payload(dtype, b[64::])

        return cls(sender, sender_time, rsvd, dlen, dtype, payload)
    
    def _serialize_payload(self) -> bytearray:
        match self.dtype:
            case 0x2 | 0x9 | 0xA: 
                res = ''
                for k, v in self.payload:
                    res += f'{k}:{Packet._serialize_int(v, 4)}'
                return res
            case 0x4 | 0x5 | 0x6: return bytearray(self.payload, encoding='utf-8')
            case _: return bytearray()

    @staticmethod
    def _parse_sender(b: bytearray) -> str:
        sender = ''
        for byte in b:
            if byte == 0:
                break
            sender += chr(byte)
        return sender

    def _parse_payload(dtype: int, b: bytearray) -> Union[None, dict[str, int], str]:
        match dtype:
            case 0x2 | 0x9 | 0xA: return { s.split(':')[0]: s.split(':')[1] for s in str(b).split(';') }
            case 0x4 | 0x5 | 0x6: return str(b, encoding='utf-8')
            case _: return None

    @staticmethod
    def _parse_number(b: bytearray) -> int:
        mul = 1
        number = 0

        for byte in reversed(b):
            number += byte * mul
            mul <<= 8

        return number

    @staticmethod
    def _parse_sender_time(b: bytearray) -> datetime.date:
        return datetime.fromtimestamp(Packet._parse_number(b))
    
    @staticmethod
    def _serialize_int(n: int, length: int) -> bytearray:
        return Packet._pad_with_zeros(Packet._int_as_bytes(n), length)
    
    @staticmethod
    def _int_as_bytes(n: int) -> bytearray:
        res = []
        while n > 0:
            res.insert(0, n & 0xff)
            n >>= 8
        return bytearray(res)

    @staticmethod
    def _pad_with_zeros(b: bytearray, length: int) -> bytearray:
        while len(b) < length:
            b.insert(0, 0x0)
        return b


# test
if __name__ == '__main__':
    def main():
        raw_packet = bytearray(
            b'User1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + # sender
            b'\x12\x34\x56\x78' + #  sender_time
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + # rsvd
            b'\x00\x00\x00\x00\x00\x00\x00\x05' + # dlen
            b'\x00\x00\x00\x04' + # dtype
            b'hello' # payload 
        )
        packet = Packet(
            'User1',
            datetime(1979, 9, 6, 0, 51, 36),
            bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
            0x5,
            0x4,
            'hello'
        )

        print(f'raw    = {raw_packet}')
        print(f'packet = {packet.to_bytearray()}')

        assert raw_packet == packet.to_bytearray()

    main()
