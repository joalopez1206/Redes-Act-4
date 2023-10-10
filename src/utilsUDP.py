import socket
from socketTCP import LEN_HEADERS, SocketTCP, DATA, SYN, ACK, FIN, SEQ

SV_ADDR = ("localhost", 8000)
BUFFER_SIZE = 16


def recvfrom_full_msg(sock: socket.socket, buffsize=LEN_HEADERS + BUFFER_SIZE):
    while True:
        msg, addr = sock.recvfrom(buffsize)
        msg = SocketTCP.parse_segment(msg.decode())[DATA]
        print(msg, end="")


def send_full_msg(sock: socket.socket, msg: bytes, addr, buffsize=BUFFER_SIZE):
    cursor = 0
    len_msg = len(msg)

    while True:
        len_of_msg_2_send = min(buffsize, len_msg - cursor)
        msg2send = msg[cursor: cursor + len_of_msg_2_send].decode()
        assert len_of_msg_2_send == len(msg2send), f"{len_of_msg_2_send} vs {len(msg2send)}"
        data_w_h = {SYN: '0', ACK: '0', FIN: '0', SEQ: '50', DATA: msg2send}
        sock.sendto(SocketTCP.create_segment(data_w_h).encode(), addr)
        cursor += len_of_msg_2_send
        if cursor >= len_msg:
            break
    return
