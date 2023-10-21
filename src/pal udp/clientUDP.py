import socket
from utilsUDP import BUFFER_SIZE, SV_ADDR, send_full_msg

client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

data: str = input()
send_full_msg(client_sock, data.encode(), SV_ADDR)
