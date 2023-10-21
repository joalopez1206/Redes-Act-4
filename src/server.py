import socketTCP
import sys
from utils import receive_full_mesage
buffsize = 12
address = (sys.argv[1], int(sys.argv[2])) 
# server
server_socketTCP = socketTCP.SocketTCP()
server_socketTCP.bind(address)

print("Esperando conexion...")
connection_socketTCP, new_address = server_socketTCP.accept()
print("Esperando recibir un mensaje")
recv_msg = receive_full_mesage(connection_socketTCP, 12, "\n")
print(f"Se recibio el mensaje {recv_msg}")
print(f"reenviando")
connection_socketTCP.send(recv_msg)

connection_socketTCP.recv_close()

