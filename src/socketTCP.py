from __future__ import annotations
import socket
import logging
BUFFER_SIZE = 16
Headers = SYN, ACK, FIN, SEQ, DATA = 'SYN', 'ACK', 'FIN', 'SEQ', 'DATA'
INB = '|||'
LEN_SYN = 10

LEN_HEADERS = 1 + 3 + 1 + 3 + 1 + 3 + 10 + 3  # numero magico

TOTAL_LEN = LEN_HEADERS + BUFFER_SIZE
logging.basicConfig(format="%(levelname)s -> %(message)s", level=logging.INFO)


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
        logging.info("-----------------------")
        logging.info("Starting three way handshake client side")
        syn_msg = self.create_msg_w_seqnum(syn=1).encode()
        # Enviamos el mensaje y
        # Esperamos que llegue el mensaje
        # y guardamos la direccion de destino
        recv = False
        msg : bytes | None = None
        while not recv:
            try:
                logging.info(f"Sending syn message: {syn_msg}")
                self.socket.sendto(syn_msg, address)
                self.socket.settimeout(5)
                msg, dest_addr = self.socket.recvfrom(TOTAL_LEN)
                recv = True
                self.dest_addr = dest_addr
            except socket.error:
                logging.info("Time out! trying again")

        # Parseamos el mensaje que llegue con SYN + ACK
        logging.info("Message recv! expecting syn+ack")
        msg_recv = SocketTCP.parse_segment(msg.decode())
        logging.info(f"{msg_recv}")
        # TODO: Chequeo de errores! (ver si es un SYN+ACK)
        assert int(msg_recv[ACK]) == 1 and int(msg_recv[SYN]) == 1  and (self.seqnum + 1) == int(msg_recv[SEQ])

        # Aumentamos el seqnum en 2 y enviamos el ack!
        self.seqnum += 2

        logging.info("Sending message ACK")
        ack_msg = self.create_msg_w_seqnum(ack=1).encode()
        logging.info(f"{ack_msg}")
        self.socket.sendto(ack_msg, dest_addr)
        logging.info("-----------------------\n")

    def accept(self):
        # Recivo el mensaje de connect
        logging.info("-----------------------")
        logging.info("Starting the threeway handshake serverside!")

        # Seteo de variables para usar despues!
        recv = False
        msg : bytes | None = None
        dest_addr = None

        msg, dest_addr = self.socket.recvfrom(TOTAL_LEN)

        #En este punnto ya llego el mensaje
        msg_recv = SocketTCP.parse_segment(msg.decode())
        assert int(msg_recv[SYN]) == 1 

        # Creamos el nuevo socket
        new_sock = SocketTCP()
        new_sock.seqnum = int(msg_recv[SEQ]) + 1

        # TODO: remover direccion hardcodeada 8003 ???
        new_address = ('localhost', 8003)

        # Y asociamos la direccion de origen y destino al nuevo socket
        new_sock.origen_addr = new_sock.socket.getsockname()
        new_sock.dest_addr = dest_addr

        # Enviamos ahora el syn+ack
        logging.info("Sending syn+ack msg")
        syn_ack_msg = new_sock.create_msg_w_seqnum(syn=1, ack=1)

        # Esperamos el ACK (STOP AND WAIT)
        recv = False
        msg = None
        # Aqui agregamos el caso extra donde si se pierde el ultimo ACK, 
        # y recibe algo con datos entonces eso cuenta como un ACK 

        while not recv:
            try:
                new_sock.socket.sendto(syn_ack_msg.encode(), dest_addr)
                logging.info(f"Enviando el syn+ack: {syn_ack_msg}")
                new_sock.socket.settimeout(5)
                logging.info(f"Esperando el ack")
                msg, _ = new_sock.socket.recvfrom(TOTAL_LEN)
                msg_recv = SocketTCP.parse_segment(msg.decode())
                logging.info(f"Mensaje recibido {msg.decode()}")
                if int(msg_recv[ACK]) == 1 or len(msg_recv[DATA]) > 0:
                    recv = True
            except socket.error:
                logging.info("Time out! trying again")
        
        assert int(msg_recv[SEQ]) == (new_sock.seqnum + 1)
        new_sock.seqnum += 1

        logging.info("Threeway handshake done!")
        logging.info("-----------------------\n")
        return new_sock, new_address

    def send(self, message: bytes):
        logging.info("-----------------------")
        logging.info("Sending the message")
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
                msg, _ = self.socket.recvfrom(TOTAL_LEN)
                parsed_msg = SocketTCP.parse_segment(msg.decode())
                #if int(parsed_msg[ACK]) != "1" or (self.seqnum + len(datastr)) != int(parsed_msg[SEQ]):
                #    continue
                received = True
            except socket.error:
                logging.info("Fallo enviar el largo del mensaje, trying denuevo")

        # Vemos si efectivamente si se aumento el largo de el datastr
        assert self.seqnum + len(datastr) == int(parsed_msg[SEQ]) and parsed_msg[ACK] == "1", f"{self.seqnum + len(datastr)} != {int(parsed_msg[SEQ])} or {parsed_msg[ACK]} != 1"
        self.seqnum += len(datastr)

        while True:
            # Aqui creamos el primer mensaje del largo
            len_of_msg_2_send = min(BUFFER_SIZE, len_msg - cursor)

            msg2send = message[cursor: cursor + len_of_msg_2_send]
            assert len_of_msg_2_send == len(msg2send), f"{len_of_msg_2_send} vs {len(msg2send)}"
            message_w_h = self.create_msg_w_seqnum(data=msg2send.decode()).encode()

            received = False
            # Stop and wait
            while not received:
                try:
                    logging.info(f"Mensaje a enviar {message_w_h}")
                    self.socket.sendto(message_w_h, self.dest_addr)
                    self.socket.settimeout(5.0)
                    msg, _ = self.socket.recvfrom(TOTAL_LEN)
                    parsed_msg = SocketTCP.parse_segment(msg.decode())
                    if (self.seqnum + len_of_msg_2_send < int(parsed_msg[SEQ])):
                        continue
                    received = True
                    assert int(parsed_msg[SEQ]) == (self.seqnum + len_of_msg_2_send), f"{int(parsed_msg[SEQ])} != {(self.seqnum + len_of_msg_2_send)}"
                except socket.error:
                    logging.info("Time out! trying again")
            self.seqnum += len_of_msg_2_send
            cursor += len_of_msg_2_send
            if cursor >= len_msg:
                break
        logging.info("Ending send")
        logging.info("-----------------------\n")

    def recv(self, buffsize: int):
        logging.info("-----------------------")
        logging.info("Starting recv")
        logging.info(f"el buffer a usar es: {buffsize}")
        original_buffsize = buffsize
        # recibimos el primer segmento
        while self.mesg_recv_so_far == 0:
            self.socket.setblocking(True)
            msg, _ = self.socket.recvfrom(TOTAL_LEN)
            parsed_msg = SocketTCP.parse_segment(msg.decode())

            #Si el mensaje ya lo vimos, entonces solo enviamos ack con nuestro numero actual
            logging.info(f"Mensaje recv! {msg} y el seqnum actual es {self.seqnum}")
            if int(parsed_msg[SEQ]) < self.seqnum:
                logging.info("Segmento duplicado! respondiendo ack")
                response = self.create_msg_w_seqnum(ack=1).encode()
                self.socket.sendto(response, self.dest_addr)
            
            else :
                largo = len(parsed_msg[DATA])
                self.mesg_recv_so_far = int(parsed_msg[DATA])
                logging.info(f"el largo del mensaje es {parsed_msg[DATA]}")
                # y enviamos el ack con el nuevo seqnum
                self.seqnum += largo
                msg = self.create_msg_w_seqnum(ack=1).encode()
                self.socket.sendto(msg, self.dest_addr)
                logging.info("Enviando el ACK")
        # aquí suponemos que es > 0 y, por lo tanto, basta con ver donde estamos
        i = 0
        data = ""
        if self.cache is not None:
            logging.info(f"Si tenia cache! el cache es : {self.cache}")
            data = self.cache + data
            buffsize -= len(self.cache)
            self.cache = None
        while i * BUFFER_SIZE < buffsize:
            self.socket.setblocking(True)
            msg, _ = self.socket.recvfrom(TOTAL_LEN)
            logging.info(f"Mensaje recv!: {msg}")
            parsed_msg = SocketTCP.parse_segment(msg.decode())
            data2add = parsed_msg[DATA]
            
            if int(parsed_msg[SEQ]) < self.seqnum:
                logging.info(f"Segmento duplicado! seqnumrecv = {int(parsed_msg[SEQ])} vs {self.seqnum} respondiendo ack")
                response = self.create_msg_w_seqnum(ack=1).encode()
                self.socket.sendto(response, self.dest_addr)
                continue
            else :
                data += data2add
                logging.info(data)
                i += 1
                self.mesg_recv_so_far -= len(data2add)
                self.seqnum += len(data2add)
                response = self.create_msg_w_seqnum(ack=1).encode()
                self.socket.sendto(response, self.dest_addr)
                if(self.mesg_recv_so_far == 0): break

        if len(data) > original_buffsize:
            self.cache = data[original_buffsize:]
            data = data[:original_buffsize]
        logging.info(f"mensaje con buffsize {original_buffsize} = {data}")
        logging.info("-----------------------\n")
        return data.encode()

    def close(self):
        
        logging.info("-----------------------")
        logging.info("Starting close function")
        
        end_of_comm_msg = self.create_msg_w_seqnum(fin=1).encode()

        logging.info(f"sending the end of comm function (fin = 1 ){self.dest_addr}")
        i = 0
        msg : bytes| None = None
        while i < 3:
            try:
                self.socket.sendto(end_of_comm_msg, self.dest_addr)
                self.socket.settimeout(5)
                msg, _ = self.socket.recvfrom(TOTAL_LEN)
                break
            except socket.error:
                logging.info(f"Error closing, trying {i+1}/3")
                i+=1
        
        
        if i < 3:
            parsed_msg = SocketTCP.parse_segment(msg.decode())
            assert int(parsed_msg[FIN]) == 1 and int(parsed_msg[ACK]) == 1 and (self.seqnum + 1) == int(parsed_msg[SEQ])
            logging.info("Recv fin+ack")
            self.seqnum += 2
            ack_msg = self.create_msg_w_seqnum(ack=1).encode()
            for _ in range(3):
                self.socket.sendto(ack_msg, self.dest_addr)
                logging.info("sending ack and ending")
        
        else:
            logging.info("3 tries, stoping connection!")
        logging.info("-----------------------")
        return

    def recv_close(self):
        logging.info("-----------------------")
        logging.info("Starting recv close ")
        self.socket.setblocking(True)
        end_of_comm_msg, _ = self.socket.recvfrom(TOTAL_LEN)
        parsed_msg = SocketTCP.parse_segment(end_of_comm_msg.decode())
        logging.info("recv")
        assert int(parsed_msg[FIN]) == 1 
        self.seqnum += 1
        ack_plus_fin_msg = self.create_msg_w_seqnum(fin=1, ack=1).encode()

        
        i = 0
        msg = None
        parsed_msg = None
        while i<3:
            try:
                self.socket.sendto(ack_plus_fin_msg, self.dest_addr)
                self.socket.settimeout(5)
                msg, _ = self.socket.recvfrom(TOTAL_LEN)
                parsed_msg = SocketTCP.parse_segment(msg.decode())
                break
            except socket.error:
                i+=1
                logging.info("ACK not received, trying again!")
        
        if i == 3:
            logging.info("ACK not recv, closing conn")
        logging.info("Ending recv close!")
        logging.info("-----------------------")

