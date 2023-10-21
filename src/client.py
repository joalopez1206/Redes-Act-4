import socketTCP
from utilsUDP import SV_ADDR
import sys

if len(sys.argv) != 3:
    print("Ussage python3 client.py <ip> <port>")

address = (sys.argv[1], int(sys.argv[2]))
s = input("Enter a message") 
s_send = s + "\n"
# client
client_socketTCP = socketTCP.SocketTCP()

client_socketTCP.connect(address)
print("Conectado! Enviando mensaje")
client_socketTCP.send(s_send.encode())
print("Enviado")
buffsize = 3000
recv_msg = client_socketTCP.recv(buffsize)
print("mensaje recibido")
assert recv_msg.decode() == s
print("Cerrando conexion")
client_socketTCP.close()