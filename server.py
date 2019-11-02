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

blockedUsers = []                    #list to keep track of all the blocked clients by username
onlineUsers = []                     #list to keep track of all online users who have been authenticated

class client:
    name = ""
    lastAction = 0
    loginAttempt = 0
    startBlockTime = 0


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
def checkBlocked(client):
    if client in blockedUsers:  #if the username is in the list of blocked users, calculate how long they have been blocked
        currentTime = time.time()
        blockedTime = currentTime - client.startBlockTime
        if blockedTime > blockDuration:      #if they have been blocked for the specified duration, remove them from the list
            blockedUsers.remove(client)
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




   
def recv_handler():
    global onlineUsers
    global blockedUsers
    global loginAttempt
    global startBlockTime

    while(1):
        #accept connection
        connectionSocket, addr = sock.accept()

        #wait for data to arrive from the client
        request = connectionSocket.recv(1024)

        #process the string to get the client's username
        clientUsername = getUsername(request)

        newClient = client()                    
        newClient.name = clientUsername
        newClient.lastAction = time.time()

        if checkBlocked(newClient) == "blocked":   #check to see if user is currently blocked
            loginResult = "Your account is blocked due to multiple login failures. Please try again later"
            connectionSocket.send(loginResult)
            connectionSocket.close()                    #close the connectionSocket if they are blocked
        elif checkBlocked(newClient) == "not blocked" and newClient not in onlineUsers: #to log in the user, check that they're not blocked and that they're not already online
            if authenticate(request) == 1:              #if the username is not blocked, check credentials.txt to see if the username & password is valid
                #onlineUsers.append(clientUsername)
                onlineUsers.append(newClient)
                loginResult = "Authenticated"
                connectionSocket.send(loginResult)      #if valid, send the result to the client
                print("%s is online" %newClient)
            else:
                newClient.loginAttempt = newClient.loginAttempt + 1     #otherwise, start counting number of login attempts if wrong password is entered
                print(newClient.loginAttempt)
                if newClient.loginAttempt == 3:
                    newClient.startBlockTime = time.time()        #block the client here; record the current time
                    blockedUsers.append(newClient)
                    print("%s is now blocked" %blockedUsers)
                    loginResult = "Invalid Password. Your account has been blocked. Please try again later"
                    connectionSocket.send(loginResult)
                    connectionSocket.close()   #close the connectionSocket. Note that the serverSocket is still alive waiting for new clients
                loginResult = "Invalid Password. Please try again"
                connectionSocket.send(loginResult)
        else:
            alreadyOnline = "You are already logged in"
            connectionSocket.send(alreadyOnline)


def send_handler():
    #global t_lock
    global clients
    global clientSocket
    global serverSocket
    global timeout
    
    while(1):
        time.sleep(5)
        print("do stuff here")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#create server socket

sock.bind(('localhost', serverPort))
#when anyone sends a packet to the given port at the IP address of the server (localhost in this case), that 
#packet will be directed to this socket.

sock.listen(1)
#The serverSocket then goes in the listen state to listen for client connection requests. 
print('Server is ready for service')


recv_thread=threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon=True
recv_thread.start()

send_thread=threading.Thread(name="SendHandler",target=send_handler)
send_thread.daemon=True
send_thread.start()
#this is the main thread
while True:
    time.sleep(0.1)





