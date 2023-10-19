import socket
import logging

BUFFER_SIZE = 16
Headers = SYN, ACK, FIN, SEQ, DATA = 'SYN', 'ACK', 'FIN', 'SEQ', 'DATA'
INB = '|||'
LEN_SYN = 10

LEN_HEADERS = 1 + 3 + 1 + 3 + 1 + 3 + 10 + 3  # numero magico
logging.basicConfig(level=logging.INFO)


class SocketTCP:
    def __init__(self):
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dest_addr: tuple[str, int] | None = None
        self.origen_addr: tuple[str, int] | None = None
        self.seqnum = 20
        self.mesg_recv_so_far = 0
        self.cache = None

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
        logging.info("Starting the threeway handshake serverside!")
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

        logging.info("Threeway handshake done!")
        return new_sock, new_address

    def send(self, message: bytes, buffsize=BUFFER_SIZE):

        # dividamos el mensaje en trozos de a lo mas 16 bytes
        cursor = 0
        len_msg = len(message)

        # Primero mensaje es el largo del mensaje
        datastr = f"{len_msg}"
        msg2send = self.create_msg_w_seqnum(data=datastr).encode()

        # lo enviamos con stop and wait
        received = False
        parsed_msg: dict | None = None
        while not received:
            try:
                self.socket.sendto(msg2send, self.dest_addr)
                # Luego tenemos que re-escribir el ack
                # y luego y actualizamos el numero de secuencia
                self.socket.settimeout(5.0)
                msg, _ = self.socket.recvfrom(LEN_HEADERS + buffsize)
                parsed_msg = SocketTCP.parse_segment(msg.decode())
                received = True
            except TimeoutError:
                logging.info("Fallo enviar el largo del mensaje, trying denuevo")

        # Vemos si efectivamente si se aumento el largo de el datastr
        assert self.seqnum + len(datastr) == int(parsed_msg[SEQ]) and parsed_msg[ACK] == "1"
        self.seqnum += len(datastr)

        while True:
            # Aqui creamos el primer mensaje del largo
            len_of_msg_2_send = min(buffsize, len_msg - cursor)

            msg2send = message[cursor: cursor + len_of_msg_2_send]
            assert len_of_msg_2_send == len(msg2send), f"{len_of_msg_2_send} vs {len(msg2send)}"
            message_w_h = self.create_msg_w_seqnum(data=msg2send.decode()).encode()

            received = False
            # Stop and wait
            while not received:
                try:
                    logging.info(message_w_h)
                    self.socket.sendto(message_w_h, self.dest_addr)
                    self.socket.settimeout(5.0)
                    msg, _ = self.socket.recvfrom(LEN_HEADERS + BUFFER_SIZE)
                    # TODO: CHECK IF ITS A ACK and if is the correct number sequence
                    received = True
                except TimeoutError:
                    logging.info("Time out! trying again")

            cursor += len_of_msg_2_send
            if cursor >= len_msg:
                break

    def recv(self, buffsize: int):
        logging.info("\n\n")
        logging.info(f"el buffer a usar es: {buffsize}")
        original_buffsize = buffsize
        # recibimos el primer segmento
        if self.mesg_recv_so_far == 0:
            msg, _ = self.socket.recvfrom(LEN_HEADERS + BUFFER_SIZE)
            parsed_msg = SocketTCP.parse_segment(msg.decode())
            largo = len(parsed_msg[DATA])
            self.mesg_recv_so_far = int(parsed_msg[DATA])
            logging.info(f"el largo es {largo}")
            # y enviamos el ack con el nuevo seqnum
            self.seqnum += largo
            msg = self.create_msg_w_seqnum(ack=1).encode()
            self.socket.sendto(msg, self.dest_addr)
            logging.info("Enviando el ACK")
        # aquí suponemos que es > 0 y, por lo tanto, basta con ver donde estamos
        logging.info("Estamos antes del cache")
        i = 0
        data = ""
        if self.cache is not None:
            logging.info(f"Si tenia cache! el cache es : {self.cache}")
            data = self.cache + data
            buffsize -= len(self.cache)
            self.cache = None
        while i * BUFFER_SIZE < buffsize:
            msg, _ = self.socket.recvfrom(LEN_HEADERS + BUFFER_SIZE)
            logging.info(msg)
            parsed_msg = SocketTCP.parse_segment(msg.decode())
            data2add = parsed_msg[DATA]

            data += data2add
            logging.info(data)
            i += 1
            self.mesg_recv_so_far -= len(data2add)
            response = self.create_msg_w_seqnum(ack=1).encode()
            self.socket.sendto(response, self.dest_addr)

        if len(data) > original_buffsize:
            self.cache = data[original_buffsize:]
            data = data[:original_buffsize]
        logging.info(f"mensaje con buffsize = {data}")
        return data.encode()
