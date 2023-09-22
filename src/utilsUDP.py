import socket

SV_ADDR = ("localhost", 8000)
BUFFER_SIZE = 16


def recvfrom_full_msg(sock: socket.socket, buffsize=BUFFER_SIZE):
    while True:
        msg, addr = sock.recvfrom(buffsize)
        print(msg.decode(), end="")


def send_full_msg(sock: socket.socket, msg: bytes, addr, buffsize=BUFFER_SIZE):
    cursor = 0
    len_msg = len(msg)
    len_of_msg_2_send = min(cursor + buffsize, len_msg)
    msg2send = msg[cursor: cursor + buffsize]
    sock.sendto(msg2send, addr)
    cursor += buffsize
    while len_of_msg_2_send < len_msg:
        len_of_msg_2_send = min(cursor + buffsize, len_msg)
        msg2send = msg[cursor: cursor + buffsize]
        sock.sendto(msg2send, addr)
        cursor += buffsize
    return
