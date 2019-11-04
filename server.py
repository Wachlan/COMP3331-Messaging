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
import thread
import threading
from threading import Thread

serverPort = int(sys.argv[1])       #port is the first command line argument
blockDuration = int(sys.argv[2])    #the duration in seconds for which a user is blocked after 3 login attempts
timeout = int(sys.argv[3])           #after this time a user will be logged out due to inactivity

blockedUsers = {}                   #Dictionary containing username and time the user was blocked
onlineUsers = {}                    #Dictionary with username and time user logged on
loginRecord = {}                    #Dictionary with username and time of login, regardless of whether they are still online
#connectionSockets = []
connectionSockets = {}

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
def checkBlocked(clientUsername):
    global blockedUsers

    if clientUsername in blockedUsers:  #if the username is in the list of blocked users, calculate how long they have been blocked
        currentTime = time.time()
        startBlockTime = blockedUsers.get(clientUsername)
        blockedTime = currentTime - startBlockTime
        if blockedTime > blockDuration:      #if they have been blocked for the specified duration, remove them from the list
            blockedUsers.pop(clientUsername)
            loginAttempt = 0                 #reset login attempt counter to 0
            result = "not blocked"
            return result
        else:                                #otherwise, they will remain in the list
            result = "blocked"
            return result
    else:                                    #if they are not in the blocked users' list, return "not blocked"
        result = "not blocked"
        return result

def endConnection(connectionSocket):
	connectionSocket.close()
	print("ending connection")

def presenceBroadcast(clientUsername, status):
    global connectionSockets

    for x in connectionSockets:
        message = "%s has logged %s\n" %(clientUsername, status)
        socket = connectionSockets.get(x)
        socket.send(message)

def whoElse(clientUsername, connectionSocket):
    global onlineUsers

    otherUsers = []

    for x in onlineUsers:
        if x != clientUsername:
            otherUsers.append(x)

    message = "Online users: %s\n" %otherUsers
    connectionSocket.send(message)

def whoElseSince(clientUsername, connectionSocket, period):
    global loginRecord
    otherUsers = []
    currentTime = time.time()

    for x in loginRecord:
        if x != clientUsername and int(currentTime - loginRecord.get(x)) <= int(period):
            otherUsers.append(x)

    message = "Other users logged on in the past %s seconds: %s" %(period, otherUsers)
    connectionSocket.send(message)

   
def recv_handler(connectionSocket):
    global onlineUsers
    global blockedUsers
    #global loginAttempt
    #global startBlockTime
    global connectionSockets
    global loginRecord

    newClient = client()
    print("new thread started")

    while(1):
        try:
            #wait for data to arrive from the client
            request = connectionSocket.recv(1024)
        except:
            print("Could not receive data")

        #process the string to get the client's username
        clientUsername = getUsername(request)

                          
        newClient.name = clientUsername
        #newClient.lastAction = time.time()
        #print("last action taken %d" newClient.lastAction)

        if checkBlocked(clientUsername) == "blocked":   #check to see if user is currently blocked
            loginResult = "Your account is blocked due to multiple login failures. Please try again later"
            try:
                connectionSocket.send(loginResult)
                connectionSocket.close()                    #close the connectionSocket if they are blocked
            except:
                print("Could not send message. Ending thread")
                thread.exit()
        elif checkBlocked(clientUsername) == "not blocked" and newClient.name not in onlineUsers: #to log in the user, check that they're not blocked and that they're not already online
            if authenticate(request) == 1:              #if the username is not blocked, check credentials.txt to see if the username & password is valid
                #onlineUsers.append(clientUsername)
                loginTime = time.time()
                onlineUsers[clientUsername] = loginTime
                loginRecord[clientUsername] = loginTime #for the whoElseSince function
                print("User %s logged in at time %s" %(clientUsername, loginTime))
                loginResult = "Authenticated\n"
                connectionSocket.send(loginResult)      #if valid, send the result to the client
                presenceBroadcast(clientUsername, "on")       #Someone has logged in, so send this result to everyone else online
                #connectionSockets.append(connectionSocket)
                connectionSockets[clientUsername] = connectionSocket

                # Start a new thread and return its identifier 
                thread.start_new_thread(messaging_handler, (connectionSocket, newClient, ))

                # Exit this thread
                thread.exit()
            else:
                newClient.loginAttempt = newClient.loginAttempt + 1     #otherwise, start counting number of login attempts if wrong password is entered
                print(newClient.loginAttempt)
                if newClient.loginAttempt == 3:
                    startBlockTime = time.time()
                    blockedUsers[clientUsername] = startBlockTime
                    print("%s is now blocked" %blockedUsers)
                    loginResult = "Invalid Password. Your account has been blocked. Please try again later\n"
                    connectionSocket.send(loginResult)
                    connectionSocket.close()   #close the connectionSocket. Note that the serverSocket is still alive waiting for new clients
                    thread.exit()
                else:
                    loginResult = "Invalid Password. Please try again"
                    try:
                        connectionSocket.send(loginResult)
                    except:
                        print("Could not send message. Ending thread")
                        thread.exit()
        else:
            alreadyOnline = "That user is already logged in"
            try:
                connectionSocket.send(alreadyOnline)
                thread.exit()
            except:
                print("Could not send message. Ending thread")
                thread.exit()

def messaging_handler(connectionSocket, newClient):
    print("Messaging thread started for %s" %newClient.name)
    timeoutTimer = threading.Timer(timeout, endConnection, [connectionSocket])

    while(1):
        """try:
            timeoutTimer.start()
            request = connectionSocket.recv(1024)
            print(request)
            timeoutTimer.cancel()
        except:
            print("Could not receive data")
            #timeoutTimer.start()            
            time.sleep(1)"""

        #print("here")
        request = connectionSocket.recv(1024)
        #print(request)
        #newClient.lastAction = time.time()
        #print("here 2")
        

        command = request.split(" ")
        #print(command[0])
        if command[0] == "logout":
            #onlineUsers.remove(newClient.name)
            del onlineUsers[newClient.name]
            #connectionSockets.remove(connectionSocket)
            del connectionSockets[newClient.name]
            presenceBroadcast(newClient.name, "off")

        if command[0] == "whoelse":
            whoElse(newClient.name, connectionSocket)

        if command[0] == "whoelsesince":
            time = command[1]
            whoElseSince(newClient.name, connectionSocket, time)
            

        


def send_handler():
    #global t_lock
    global clients
    global clientSocket
    global serverSocket
    global timeout
    
    while(1):
        time.sleep(5)
        print("do stuff here")

########################################################################################################################################

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#create server socket

sock.bind(('localhost', serverPort))
#when anyone sends a packet to the given port at the IP address of the server (localhost in this case), that 
#packet will be directed to this socket.

sock.listen(1)
#The serverSocket then goes in the listen state to listen for client connection requests. 
print('Server is ready for service')

#this is the main thread
while True:
    #time.sleep(0.1)

    #accept connection
    connectionSocket, addr = sock.accept()

    # Start a new thread and return its identifier 
    thread.start_new_thread(recv_handler, (connectionSocket, )) 





