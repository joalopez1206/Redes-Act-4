import socket

Headers = SYN, ACK, FIN, SEQ, DATOS = 'SYN', 'ACK', 'FIN', 'SEQ', 'DATOS'
INB = '|||'


class SocketTCP:
    def __int__(self):
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dest_addr: tuple[str, int] = None
        self.origen_addr: tuple[str, int] = None
        self.seqnum = 0

    @staticmethod
    def parse_segment(segmento: str):
        temp = segmento.split(INB)
        return {k: v for k, v in zip(Headers, temp)}

    @staticmethod
    def create_segment(struct: dict):
        temp = []
        for k in Headers:
            temp += [struct[k]]
        return INB.join(temp)
