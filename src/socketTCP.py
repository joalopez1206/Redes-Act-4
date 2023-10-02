import socket

Headers = SYN, ACK, FIN, SEQ, DATA = 'SYN', 'ACK', 'FIN', 'SEQ', 'DATA'
INB = '|||'
LEN_SYN = 10

LEN_HEADERS = 1 + 3 + 1 + 3 + 1 + 3 + 10 + 3  # numero magico


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
            if k == SEQ:
                temp += [SocketTCP.add_len_zeros(struct[k])]
            else:
                temp += [struct[k]]
        return INB.join(temp)

    @staticmethod
    def add_len_zeros(seq_num: int, len_seq=LEN_SYN):
        return f"{seq_num:0>{len_seq}}"
