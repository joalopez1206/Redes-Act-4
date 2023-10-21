import socketTCP
from utilsUDP import SV_ADDR
from utils import contains_end_of_message, remove_end_of_message, receive_full_mesage
buffsize = 12

# server
server_socketTCP = socketTCP.SocketTCP()
server_socketTCP.bind(SV_ADDR)

print("Esperando conexion...")
connection_socketTCP, new_address = server_socketTCP.accept()
print("Esperando recibir un mensaje")
recv_msg = receive_full_mesage(connection_socketTCP, 12, "\n")
print(f"Se recibio el mensaje {recv_msg}")
print(f"reenviando")
connection_socketTCP.send(recv_msg)

connection_socketTCP.recv_close()

