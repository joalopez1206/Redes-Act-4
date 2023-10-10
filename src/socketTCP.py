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
        # y guardamos la direccion de destino
        msg, dest_addr = self.socket.recvfrom(LEN_HEADERS)
        self.dest_addr = dest_addr

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
        self.socket.sendto(ack_msg, dest_addr)

    def accept(self):
        # Recivo el mensaje de connect
        logging.info("Waiting for syn message")
        msg, dest_addr = self.socket.recvfrom(LEN_HEADERS)

        msg_recv = SocketTCP.parse_segment(msg.decode())
        logging.info(f"{msg_recv}")
        # TODO: chequeo de errores! (ver si es un SYN)
        new_sock = SocketTCP()
        new_sock.seqnum = int(msg_recv[SEQ]) + 1

        # TODO: remover direccion hardcodeada 8003
        new_address = ('localhost', 8003)
        new_sock.origen_addr = new_address
        new_sock.dest_addr = dest_addr

        # Enviamos ahora el syn+ack
        logging.info("Sending syn+ack msg")
        syn_ack_msg = new_sock.create_msg_w_seqnum(syn=1, ack=1)
        logging.info(f"{syn_ack_msg}")
        new_sock.socket.sendto(syn_ack_msg.encode(), dest_addr)

        # Esperamos el ACK
        msg, _ = new_sock.socket.recvfrom(LEN_HEADERS)

        logging.info("Message received!")
        msg_recv = SocketTCP.parse_segment(msg.decode())
        logging.info(f"{msg_recv}")

        # TODO: chequear errores! (ver si es ACK)
        assert int(msg_recv[SEQ]) == (new_sock.seqnum + 1)

        new_sock.seqnum += 1
        return new_sock, new_address

    def send(self, message, buffsize=16):

        # dividamos el mensaje en trozos de a lo mas 16 bytes
        cursor = 0
        len_msg = len(message)

        # Primero mensaje es el largo del mensaje
        datastr = f"{len_msg}"
        msg2send = SocketTCP.create_msg_w_seqnum(data=datastr)

        # lo enviamos
        self.socket.sendto(msg2send, self.dest_addr)

        # Luego tenemos que reecibir el ack
        # y luego y actualizamos el numero de secuencia
        msg, _ = self.socket.recvfrom(LEN_HEADERS+buffsize)

        parsed_msg = SocketTCP.parse_segment(msg.decode())

        # Vemos si efectivamente si se aumento el largo de el datastr
        assert self.seqnum+len(datastr) == int(parsed_msg[SEQ])
        self.seqnum += len(datastr)


        while True:
            ## Aqui creamos el primer mensaje del largo
            len_of_msg_2_send = min(buffsize, len_msg - cursor)

            msg2send = message[cursor: cursor + len_of_msg_2_send]
            assert len_of_msg_2_send == len(msg2send), f"{len_of_msg_2_send} vs {len(msg2send)}"
            data_w_h = {SYN: '0', ACK: '0', FIN: '0', SEQ: '50', DATA: msg2send}
            self.socket.sendto(SocketTCP.create_segment(data_w_h).encode(), addr)
            cursor += len_of_msg_2_send
            if cursor >= len_msg:
                break

    def recv(self, buffsize):
        ...
