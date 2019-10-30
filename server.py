#Python 3
#Lachlan Chow z5164192
#run with python server.py server_port block_duration timeout

#server_port:  port number which the server will use to communicate with the clients
#block_duration:  this is the duration in seconds for which a user should be blocked after three unsuccessful authentication attempts
#timeout: this is the duration in seconds of inactivity after which a user is logged off by the server

#A good place to start would be to implement the functionality to allow a single user to
#login with the server. Next, add the blocking functionality for 3 unsuccessful attempts
#You could then proceed to the timeout functionality (i.e. automatically logout a user after inactivity. 

import sys  #contains the command-line arguments passed to the script
import socket
import time
import threading

serverPort = int(sys.argv[1])       #port is the first command line argument
blockDuration = int(sys.argv[2])    #the duration in seconds for which a user is blocked after 3 login attempts
timeout = int(sys.argv[3])           #after this time a user will be logged out due to inactivity

loginAttempt = 0
blockedUsers = []                    #list to keep track of all the blocked clients by username
onlineUsers = []                     #list to keep track of all online users who have been authenticated

#takes in a username & password combination, returns the username
def getUsername(loginRequest):
    loginRequestList = loginRequest.split(" ")
    username = loginRequestList[0]
    return username

#check if username password combination exists in credentials.txt
#returns 1 if valid combination and 0 if not valid
def authenticate(loginDetails):
    f = open('credentials.txt', "r") #open the file
    contents = f.read() #read the file
    f.close()

    if loginDetails in contents:
        return 1
    else:
        return 0

#Checks if the username of a client is currently blocked
def checkBlocked(username):
    if username in blockedUsers:  #if the username is in the list of blocked users, calculate how long they have been blocked
        currentTime = time.time()
        blockedTime = currentTime - startBlockTime
        if blockedTime > blockDuration:      #if they have been blocked for the specified duration, remove them from the list
            blockedUsers.remove(username)
            loginAttempt = 0                 #reset login attempt counter to 0
            result = "not blocked"
            return result
        else:                                #otherwise, they will remain in the list
            result = "blocked"
            return result
    else:                                    #if they are not in the blocked users' list, return "not blocked"
        result = "not blocked"
        return result

def endConnection():
	connectionSocket.close()
	print("ending connection")

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

    #wait for data to arrive from the client
    request = connectionSocket.recv(1024)

    #the time of the user's most recent request
    timeoutTimer = threading.Timer(timeout, endConnection)
    #timeoutTimer.start()

    #process the string to get the client's username
    clientUsername = getUsername(request)

    if checkBlocked(clientUsername) == "blocked":   #check to see if user is currently blocked
        loginResult = "Your account is blocked due to multiple login failures. Please try again later"
        connectionSocket.send(loginResult)
        connectionSocket.close()                    #close the connectionSocket if they are blocked
    elif checkBlocked(clientUsername) == "not blocked" and clientUsername not in onlineUsers: #to log in the user, check that they're not blocked and that they're not already online
        if authenticate(request) == 1:              #if the username is not blocked, check credentials.txt to see if the username & password is valid
            onlineUsers.append(clientUsername)
            loginResult = "Authenticated"
            connectionSocket.send(loginResult)      #if valid, send the result to the client
            print("%s is online" %onlineUsers)
        else:
            loginResult = "Invalid Password. Please try again"
            loginAttempt = loginAttempt + 1         #otherwise, start counting number of login attempts if wrong password is entered
            if loginAttempt == 3:
                startBlockTime = time.time()        #block the client here; record the current time
                blockUsername = getUsername(request)#get the username of the client to be blocked
                blockedUsers.append(blockUsername)  #add the username to the list of blocked users
                print(blockedUsers)
                loginResult = "Invalid Password. Your account has been blocked. Please try again later"
            connectionSocket.send(loginResult)
            connectionSocket.close()   #close the connectionSocket. Note that the serverSocket is still alive waiting for new clients
    else:
        print("You are already logged in")


  
