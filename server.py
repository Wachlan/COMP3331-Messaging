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
from collections import defaultdict

serverPort = int(sys.argv[1])       #port is the first command line argument
blockDuration = int(sys.argv[2])    #the duration in seconds for which a user is blocked after 3 login attempts
timeout = int(sys.argv[3])           #after this time a user will be logged out due to inactivity

blockedUsers = {}                   #Dictionary containing username and time the user was blocked
onlineUsers = {}                    #Dictionary with username and time user logged on
loginRecord = {}                    #Dictionary with username and time of login, regardless of whether they are still online
connectionSockets = {}              #Dictionary with username and socket connection
offlineMessages = defaultdict(list)  #list backed multidictionary to store messages for offline users
blacklistedUsers = defaultdict(list)  #list backed multidictionary to store which clients have blocked each other

#counter = 0
#clientList = []

class client:
    name = ""
    lastAction = 0
    loginAttempt = 0
    blacklist = []

    #def addBlacklist(self, name):
    #    self.blacklist.append(name)


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

def presenceBroadcast(newClient, status):
    global connectionSockets
    global blacklistedUsers

    for users in connectionSockets:
        if newClient.name in blacklistedUsers[users]:
            continue

        if users in blacklistedUsers[newClient.name]:
            continue

        else:
            message = "%s has logged %s\n" %(newClient.name, status)
            socket = connectionSockets.get(users)
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
    global time

    otherUsers = []
    currentTime = time.time()

    for x in loginRecord:
        if x != clientUsername and int(currentTime - loginRecord.get(x)) <= int(period):
            otherUsers.append(x)

    message = "Other users logged on in the past %s seconds: %s" %(period, otherUsers)
    connectionSocket.send(message)

"""def broadcast(clientUsername, message):
    global connectionSockets

    for x in connectionSockets:
        if x != clientUsername:
            socket = connectionSockets.get(x)
            joinedMessage = " ".join(message)
            socket.send(joinedMessage)"""

def broadcast(newClient, message):
    global connectionSockets
    global blacklistedUsers
    senderSocket = connectionSockets.get(newClient.name)
    errorMessageFlag = 0

    for users in connectionSockets:
        if newClient.name in blacklistedUsers[users]:
            errorMessageFlag = 1
            continue
        if users in blacklistedUsers[newClient.name]:     #similarly, if someone has blocked a client, they cannot broadcast to them
            errorMessageFlag = 1
            continue
        if users != newClient.name:
            socket = connectionSockets.get(users)
            joinedMessage = " ".join(message)
            socket.send(joinedMessage)

    if errorMessageFlag == 1:
        errorMessage = "Your message could not be delievered to some recipients"
        senderSocket.send(errorMessage)

        
"""def sendMessage(sender, receiver, message):
    global connectionSockets
    global offlineMessages

    if str(receiver) == str(sender):
        senderSocket = connectionSockets.get(sender)
        errorMessage = "Error: You cannot message yourself"
        senderSocket.send(errorMessage)

    elif receiver in connectionSockets:
        receiverSocket = connectionSockets.get(receiver)
        joinedMessage = "%s: " %sender + " ".join(message) + "\n"
        receiverSocket.send(joinedMessage)

    elif authenticate(receiver) == 1:
        senderSocket = connectionSockets.get(sender)
        #If the receiver is offline then store the message
        joinedMessage = "%s: " %sender + " ".join(message)
        offlineMessages[receiver].append(joinedMessage)
        #print(offlineMessages)
        errorMessage = "Error: %s is not online. Message has been stored" %receiver
        senderSocket.send(errorMessage)
        print("store message here")

    elif authenticate(receiver) == 0:
        senderSocket = connectionSockets.get(sender)
        errorMessage = "Error: This user does not exist"
        senderSocket.send(errorMessage)"""

def sendMessage(newClient, receiver, message):
    global connectionSockets
    global offlineMessages
    global blacklistedUsers

    senderSocket = connectionSockets.get(newClient.name)
    receiverSocket = connectionSockets.get(receiver)

    #print("%s is trying to send a message to %s" %(newClient.name, receiver))

    if str(receiver) == str(newClient.name):
        errorMessage = "Error: You cannot message yourself"
        senderSocket.send(errorMessage)

    #elif receiver in newClient.blacklist:
        #errorMessage = "Error: You have blocked this user"
        #senderSocket.send(errorMessage)

    #elif newClient.name in blacklistedUsers and blacklistedUsers[newClient.name] != None:
       # if receiver in blacklistedUsers[newClient.name]:
         #   errorMessage = "Error: This user is blocked"
         #   senderSocket.send(errorMessage)

   # elif receiver in blacklistedUsers and blacklistedUsers[receiver] != None:
    #    if newClient.name in blacklistedUsers[receiver]:
      #      errorMessage = "Error: This user is blocked"
         #   senderSocket.send(errorMessage)

    elif receiver in blacklistedUsers[newClient.name]:
            errorMessage = "Error: This user is blocked"
            senderSocket.send(errorMessage)

    elif newClient.name in blacklistedUsers[receiver]:
            errorMessage = "Error: This user is blocked"
            senderSocket.send(errorMessage)

    elif receiver in connectionSockets:
        joinedMessage = "%s: " %newClient.name + " ".join(message) + "\n"
        receiverSocket.send(joinedMessage)

    elif authenticate(receiver) == 1:
        print("store message here")
        #If the receiver is offline then store the message
        joinedMessage = "%s: " %newClient.name + " ".join(message)
        offlineMessages[receiver].append(joinedMessage)
        errorMessage = "Error: %s is not online. Message has been stored" %receiver
        senderSocket.send(errorMessage)

    elif authenticate(receiver) == 0:
        errorMessage = "Error: This user does not exist"
        senderSocket.send(errorMessage)

    else:
        errorMessage = "Error: Message could not be delivered"
        senderSocket.send(errorMessage)

def blacklistUser(newClient, bully):
    global connectionSockets
    senderSocket = connectionSockets.get(newClient.name)

    #print("client object passed in is %s" %newClient)

    if str(bully) == str(newClient.name):
        errorMessage = "Error: You cannot blacklist yourself"
        senderSocket.send(errorMessage)

    elif authenticate(bully) == 1:
        #newClient.blacklist.append(bully)  #add the blacklisted user to the client's list
        #newClient.addBlackList(bully)
        blacklistedUsers[newClient.name].append(bully)    #the client can't send messages to the bully now
        blacklistedUsers[bully].append(newClient.name)    #the bully can't send messages to the client now
        print("%s and %s can't message each other now" %(bully, blacklistedUsers[bully]))
        Message = "%s has been blacklisted" %bully
        senderSocket.send(Message)

    elif authenticate(bully) == 0:
        errorMessage = "Error: This user does not exist"
        senderSocket.send(errorMessage)

def unblacklistUser(newClient, bully):
    global connectionSockets
    senderSocket = connectionSockets.get(newClient.name)

    if str(bully) == str(newClient.name):
        errorMessage = "Error: You cannot unblock yourself"
        senderSocket.send(errorMessage)

    #elif bully in newClient.blacklist:
        #newClient.blacklist.remove(bully)            #remove the blocked user from the client's list
    #elif bully in blacklistedUsers[newClient.name]:
        #blacklistedUsers[newClient.name].remove(bully)
        #blacklistedUsers[bully].remove(newClient.name)
        #if newClient.name in blacklistedUsers[bully]:
            #blacklistedUsers[bully].remove(newClient.name)
            #print("blocked clients %s" %blacklistedUsers[bully])
        #Message = "%s has been unblocked" %bully
        #senderSocket.send(Message)

    elif bully in blacklistedUsers[newClient.name]:
        blacklistedUsers[newClient.name].remove(bully)
        blacklistedUsers[bully].remove(newClient.name)
        Message = "%s has been unblocked" %bully
        senderSocket.send(Message)
        print(blacklistedUsers)

    elif authenticate(bully) == 1:
        errorMessage = "Error: This user is not currently blocked"
        senderSocket.send(errorMessage)

    elif authenticate(bully) == 0:
        errorMessage = "Error: This user does not exist"
        senderSocket.send(errorMessage)

    else:
        errorMessage = "Error: Action unavailable"
        senderSocket.send(errorMessage)

   
def recv_handler(connectionSocket):
    global onlineUsers
    global blockedUsers
    global connectionSockets
    global loginRecord
    #global counter
    global clientList

    newClient = client()
    #counter = counter + 1
    #clientList.append(newClient)
    #print("client list has %s" %clientList)

    while(1):
        #global clientList
        global onlineUsers
        global time

        try:
            #wait for data to arrive from the client
            request = connectionSocket.recv(1024)
        except:
            print("Could not receive data")
            thread.exit()

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
                #loginTime = 0
                #loginTime = time.time()
                #onlineUsers[clientUsername] = loginTime
                #loginRecord[clientUsername] = loginTime #for the whoElseSince function"""
                onlineUsers[clientUsername] = time.time()
                loginRecord[clientUsername] = time.time() #for the whoElseSince function
                #print("User %s logged in at time %s" %(clientUsername, loginTime))
                #print(onlineUsers)
                loginResult = "Authenticated"
                connectionSocket.send(loginResult)      #if valid, send the result to the client
                time.sleep(0.2)
                presenceBroadcast(newClient, "on")       #Someone has logged in, so send this result to everyone else online
                #send the user that just logged on their offline messages
                if clientUsername in offlineMessages:
                    for x in offlineMessages[clientUsername]:
                        x = x + "\n"
                        connectionSocket.send(x)        #send the messages received offline to the user
                    del offlineMessages[clientUsername] #once the messages have been sent, remove the messages from storage
                connectionSockets[clientUsername] = connectionSocket

                """# Start a new thread and return its identifier 
                #thread.start_new_thread(messaging_handler, (connectionSocket, newClient, ))
                clientObject = clientList[counter-1]
                thread.start_new_thread(messaging_handler, (connectionSocket, clientObject, ))

                # Exit this thread
                thread.exit()"""


                print("Messaging thread started for %s" %newClient.name)
                print("blacklisted users are %s" %newClient.blacklist)
                while(1):
                    #global onlineUsers
                    #global blockedUsers
                    #global connectionSockets
                    #global loginRecord
                    #global counter
                    #global clientList

                    timeoutTimer = threading.Timer(timeout, endConnection, [connectionSocket])
 
                    try:
                        timeoutTimer.start()
                        #print("timer started")
                    except:
                        print("couldn't start timer")
                        thread.exit()

                    try:
                        request = connectionSocket.recv(1024)
                    except:
                        thread.exit()
                        print("thread shutting down")

                    timeoutTimer.cancel()


                    command = request.split(" ")

                    if command[0] == "logout":
                        del onlineUsers[newClient.name]
                        del connectionSockets[newClient.name]
                        presenceBroadcast(newClient, "off")
                        message = "You have been logged out\n"
                        connectionSocket.send(message)
                        thread.exit()

                    elif command[0] == "whoelse":
                       whoElse(newClient.name, connectionSocket)

                    elif command[0] == "whoelsesince":
                       period = command[1]
                       whoElseSince(newClient.name, connectionSocket, period)

                    elif command[0] == "broadcast":
                        message = command[1:]
                        broadcast(newClient, message)
        
                    elif command[0] == "message":
                        user = command[1]
                        message = command[2:]
                        sendMessage(newClient, user, message)

                    elif command[0] == "block":
                        user = command[1]                #get the name of the user to be blocked
                        blacklistUser(newClient, user)   #block this user

                    elif command[0] == "unblock":
                        user = command[1]                  #get the name of the user to be unblocked
                        unblacklistUser(newClient, user)   #unlock this user

                    else:
                        message = "Error: Invalid command"
                        try:
                            connectionSocket.send(message)
                        except:
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

"""
recv_thread=threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon=True
recv_thread.start()

send_thread=threading.Thread(name="SendHandler",target=send_handler)
send_thread.daemon=True
send_thread.start()
"""

#this is the main thread
while True:
    #time.sleep(0.1)

    #accept connection
    connectionSocket, addr = sock.accept()

    # Start a new thread and return its identifier 
    thread.start_new_thread(recv_handler, (connectionSocket, )) 





