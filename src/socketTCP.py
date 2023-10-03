import socket
import logging

Headers = SYN, ACK, FIN, SEQ, DATA = 'SYN', 'ACK', 'FIN', 'SEQ', 'DATA'
INB = '|||'
LEN_SYN = 10

LEN_HEADERS = 1 + 3 + 1 + 3 + 1 + 3 + 10 + 3  # numero magico
logging.basicConfig(level=logging.INFO)


class SocketTCP:
    def __init__(self):
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dest_addr: tuple[str, int] = None
        self.origen_addr: tuple[str, int] = None
        self.seqnum = 20

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

    def bind(self, address):
        self.origen_addr = address
        self.socket.bind(address)

    @staticmethod
    def create_msg(syn=0, ack=0, fin=0, seq=0, data=""):
        return SocketTCP.create_segment({SYN: str(syn), ACK: str(ack), FIN: str(fin), SEQ: str(seq), DATA: str(data)})

    def create_msg_w_seqnum(self, syn=0, ack=0, fin=0, data=""):
        return SocketTCP.create_msg(syn=syn, ack=ack, fin=fin, seq=self.seqnum, data=data)

    def connect(self, address):
        logging.info("Starting three way handshake client side")
        syn_msg = self.create_msg_w_seqnum(syn=1).encode()
        # Enviamos el mensaje
        logging.info(f"Sending syn message: {syn_msg}")
        self.socket.sendto(syn_msg, address)
        # Esperamos que llegue el mensaje
        msg, _ = self.socket.recvfrom(LEN_HEADERS)

        # Parseamos el mensaje que llegue con SYN + ACK
        logging.info("Message recv! expecting syn+ack")
        msg_recv = SocketTCP.parse_segment(msg.decode())
        logging.info(f"{msg_recv}")
        # TODO: Chequeo de errores! (ver si es un SYN+ACK)
        assert (self.seqnum + 1) == int(msg_recv[SEQ])

        # Aumentamos el seqnum en 2 y enviamos el ack!
        self.seqnum += 2

        logging.info("Sending message ACK")
        ack_msg = self.create_msg_w_seqnum(ack=1).encode()
        logging.info(f"{ack_msg}")
        self.socket.sendto(ack_msg, address)

    def accept(self):
        # Recivo el mensaje de connect
        logging.info("Waiting for syn message")
        msg, dest_addr = self.socket.recvfrom(LEN_HEADERS)

        msg_recv = SocketTCP.parse_segment(msg.decode())
        logging.info(f"{msg_recv}")
        # TODO: chequeo de errores! (ver si es un SYN)
        self.seqnum = int(msg_recv[SEQ]) + 1

        new_sock = SocketTCP()

        # TODO: remover direccion hardcodeada 8003
        new_address = ('localhost', 8003)
        new_sock.origen_addr = new_address
        new_sock.dest_addr = dest_addr

        # Enviamos ahora el syn+ack
        logging.info("Sending syn+ack msg")
        syn_ack_msg = self.create_msg_w_seqnum(syn=1, ack=1)
        logging.info(f"{syn_ack_msg}")
        self.socket.sendto(syn_ack_msg.encode(), dest_addr)

        # Esperamos el ACK
        msg, _ = self.socket.recvfrom(LEN_HEADERS)

        logging.info("Message received!")
        msg_recv = SocketTCP.parse_segment(msg.decode())
        logging.info(f"{msg_recv}")
        # TODO: chequear errores! (ver si es ACK)
        assert int(msg_recv[SEQ]) == (self.seqnum + 1)

        self.seqnum += 1

        new_sock.seqnum = self.seqnum
        return new_sock, new_address
