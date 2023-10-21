from utilsUDP import SV_ADDR, recvfrom_full_msg
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(SV_ADDR)

recvfrom_full_msg(server_socket)
