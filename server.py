#Python 3
#Lachlan Chow z5164192
#run with python server.py server_port block_duration timeout

#server_port:  port number which the server will use to communicate with the clients
#block_duration:  this is the duration in seconds for which a user should be blocked after three unsuccessful authentication attempts
#timeout: this is the duration in seconds of inactivity after which a user is logged off by the server

#A good place to start would be to implement the functionality to allow a single user to
#login with the server. Next, add the blocking functionality for 3 unsuccessful attempts

import sys  #contains the command-line arguments passed to the script
import socket

serverPort = int(sys.argv[1])       #port is the first command line argument
blockDuration = int(sys.argv[2])    #the duration in seconds for which a user is blocked after 3 login attempts
timeout = int(sys.argv[3])           #after this time a user will be logged out due to inactivity

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#create server socket

sock.bind(('localhost', serverPort))
#when anyone sends a packet to the given port at the IP address of the server (localhost in this case), that 
#packet will be directed to this socket.

sock.listen(1)
#The serverSocket then goes in the listen state to listen for client connection requests. 


while 1:
    connectionSocket, addr = sock.accept()
    #When a client knocks on this door, the program invokes the accept( ) method for serverSocket,
    #which creates a new socket in the server, called connectionSocket, dedicated to this particular 
    #client. The client and server then complete the handshaking, creating a TCP connection between 
    #the client?s clientSocket and the server?s connectionSocket. With the TCP connection established,
    #the client and server can now send bytes to each other over the connection. With TCP, all bytes 
    #sent from one side not are not only guaranteed to arrive at the other side but also guaranteed to arrive in order

    request = connectionSocket.recv(1024)
    #wait for data to arrive from the client

    f = open('credentials.txt', "r") #open the file
    contents = f.read() #read the file
    f.close()

    if request in contents:
        loginResult = "Authenticated, you in bitch!"
    else:
        loginResult = "Invalid Password. Please try again"

    connectionSocket.send(loginResult)












