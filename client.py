#Python 3
#Lachlan Chow z5164192
#run with python client.py server_IP server_port

#server_IP: this is the IP address of the machine on which the server is running.
#server_port: this is the port number being used by the server. This argument should be the same as the first argument of the server.

import sys  #contains the command-line arguments passed to the script
import socket
import threading
import time

serverIP = str(sys.argv[1])
serverPort = int(sys.argv[2])

def recv_handler():
    username = raw_input('Username:')
#raw_input() is a built-in function in Python. When this command is executed, the user at the client is prompted with
#the words ?Username:? The user then uses the keyboard to input a line, which is put into the 
#variable sentence. Now that we have a socket and a message, we will want to send the message through the socket
#to the destination host.

    password = raw_input('Password:')

    loginDetails = username + " " + password

    sock.send(loginDetails)
#As the connection has already been established, the client program simply drops the bytes in the string sentence 
#into the TCP connection. Note the difference between UDP sendto() and TCP send() calls. In TCP we do not need to 
#attach the destination address to the packet, as was the case with UDP sockets.

    while(1):
        infoReceived = sock.recv(1024)
        print(infoReceived)
        #print("rec handler loop")


def send_handler():
    time.sleep(3)
    while(1):
        command = raw_input('Command:')
        sock.send(command)
        #print("send handler loop")


# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = (serverIP, serverPort)
sock.connect(server_address)

recv_thread=threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon=True
recv_thread.start()

send_thread=threading.Thread(name="SendHandler",target=send_handler)
send_thread.daemon=True
send_thread.start()

#this is the main thread
while True:
    time.sleep(0.1)
