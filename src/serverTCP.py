import socketTCP
from utilsUDP import SV_ADDR

# server
server_socketTCP = socketTCP.SocketTCP()
server_socketTCP.bind(SV_ADDR)
connection_socketTCP, new_address = server_socketTCP.accept()