#Python 2
#Lachlan Chow z5164192
#run with python client.py server_IP server_port

#server_IP: this is the IP address of the machine on which the server is running.
#server_port: this is the port number being used by the server. This argument should be the same as the first argument of the server.

import sys  #contains the command-line arguments passed to the script
import socket
import time
import thread
import threading
from threading import Thread

serverIP = str(sys.argv[1])
serverPort = int(sys.argv[2])

username = "" #client's username

def login_handler():
    global username
    
    while(1):

        username = raw_input('Username:')  #send username to the server
        sock.send(username)
        infoReceived = sock.recv(1024)

        if infoReceived == "valid username":  #if valid username, break loop to enter password
        	break
        elif infoReceived == "invalid username":
        	print("Invalid Username: Please retry")
        	continue

    while(1):
        password = raw_input('Password:')  #send password to the server
        loginDetails = username + " " + password
        sock.send(loginDetails)

        infoReceived = sock.recv(1024)
        print(infoReceived)
        if infoReceived == "Authenticated":  #if authenticated, go onto messaging thread
            thread.start_new_thread(messaging_handler, (sock, ))
            thread.exit()
        elif infoReceived == "Invalid Password. Your account has been blocked. Please try again later":
            exit()
        else:
            continue

def messaging_handler(sock):
    thread.start_new_thread(recv_handler, (sock, ))
    while(1):
        command = raw_input('')  #allow users to enter commands
        sock.send(command)

def recv_handler(sock):  #separate thread to print any information received from server
    while(1):
        infoReceived = sock.recv(1024)
        print(infoReceived)


# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = (serverIP, serverPort)
sock.connect(server_address)

recv_thread=threading.Thread(name="LoginHandler", target=login_handler)
recv_thread.daemon=True
recv_thread.start()


#this is the main thread
while True:
    time.sleep(0.1)

