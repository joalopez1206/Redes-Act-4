import socketTCP
from utilsUDP import SV_ADDR
# client
client_socketTCP = socketTCP.SocketTCP()
client_socketTCP.connect(SV_ADDR)