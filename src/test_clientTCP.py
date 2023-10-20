import time

from socketTCP import SocketTCP
from utilsUDP import SV_ADDR
# CLIENT
client_socketTCP = SocketTCP()
client_socketTCP.connect(SV_ADDR)
# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message)
# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)
# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)

#time.sleep(2.0)
client_socketTCP.close()
