import socket
import sys

server_socket = socket.socket();
server_socket.bind(('localhost', int(sys.argv[1])))
server_socket.listen(5)
while True:
    (new_sock, address) = server_socket.accept()
    msg = new_sock.recv(1024)
    print(msg)