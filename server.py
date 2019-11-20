#Python 2
#Lachlan Chow z5164192
#run with python server.py server_port block_duration timeout

#server_port:  port number which the server will use to communicate with the clients
#block_duration:  this is the duration in seconds for which a user should be blocked after three unsuccessful authentication attempts
#timeout: this is the duration in seconds of inactivity after which a user is logged off by the server


import sys  #contains the command-line arguments passed to the script
import socket
import time
import thread
import threading
from threading import Thread
from collections import defaultdict

serverPort = int(sys.argv[1])        #port is the first command line argument
blockDuration = int(sys.argv[2])     #the duration in seconds for which a user is blocked after 3 login attempts
timeout = int(sys.argv[3])           #after this time a user will be logged out due to inactivity

t_lock=threading.Condition()         #thread lock to prevent 2 threads from changing the same global variable simultaneously

blockedUsers = {}                     #Dictionary containing username and time the user was blocked
onlineUsers = {}                      #Dictionary with username and time user logged on
loginRecord = {}                      #Dictionary with username and time of login, regardless of whether they are still online
connectionSockets = {}                #Dictionary with username and socket connection
#multidict programming learned from https://multidict.readthedocs.io/en/stable/multidict.html#multidict
offlineMessages = defaultdict(list)   #list backed multidictionary to store messages for offline users
blacklistedUsers = defaultdict(list)  #list backed multidictionary to store which clients have blocked each other
validUsernames = []                   #list containing all of possible valid usernames from credentials.txt

class client:                         #client class to keep track of the client in each thread
    name = ""
    loginAttempt = 0

#opens credentials.txt and puts all the usernames into the validUsernames list
#code adapted from https://stackoverflow.com/questions/23372086/how-would-i-read-only-the-first-word-of-each-line-of-a-text-file
#function syntax learned from https://www.learnpython.org/en/Functions
def fillvalidUsernames():
    global validUsernames

    with open('credentials.txt', 'r') as f:
        validUsernames = [line.split(None, 1)[0] for line in f]

#checks if a given usernameis valid
def checkvalidUsername(username):
    global validUsernames

    if username in validUsernames:
        return "valid"
    else:
        return "invalid"

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

#function to do presence broadcasts
def presenceBroadcast(newClient, status):
    global connectionSockets
    global blacklistedUsers

    for users in connectionSockets:          #go through dictionary of online users
        if newClient.name in blacklistedUsers[users]:   #if clients have blocked each other, do not broadcast presence
            continue

        if users in blacklistedUsers[newClient.name]:
            continue

        else:
            message = "%s has logged %s" %(newClient.name, status)  #declaring that a user has logged on or off
            socket = connectionSockets.get(users)
            socket.send(message)

#function for the whoelse command
def whoElse(clientUsername, connectionSocket):
    global onlineUsers
    otherUsers = []

    for x in onlineUsers: #for all other online users, notify them about the client
        if x != clientUsername:
            otherUsers.append(x)

    message = "Online users: %s" %otherUsers
    connectionSocket.send(message)

#function for the whoelsesince command
def whoElseSince(clientUsername, connectionSocket, period):
    global loginRecord
    global time

    otherUsers = []
    currentTime = time.time()

    #using the dictionary of login times, if the currenttime - login time is less than the requested period, put the username into a list
    for x in loginRecord:
        if x != clientUsername and int(currentTime - loginRecord.get(x)) <= int(period):
            otherUsers.append(x)

    message = "Other users logged on in the past %s seconds: %s" %(period, otherUsers)
    connectionSocket.send(message)

#function for the broadcast command
def broadcast(newClient, message):
    global connectionSockets
    global blacklistedUsers
    senderSocket = connectionSockets.get(newClient.name)
    errorMessageFlag = 0 #to avoid repeating the message that "Your message could not be delievered to some recipients"

    for users in connectionSockets:
        if newClient.name in blacklistedUsers[users]: #If someone has blocked a client, they cannot broadcast to them
            errorMessageFlag = 1
            continue
        if users in blacklistedUsers[newClient.name]:
            errorMessageFlag = 1
            continue
        if users != newClient.name:
            socket = connectionSockets.get(users)
            joinedMessage = "%s: " %newClient.name + " ".join(message)
            socket.send(joinedMessage)

    if errorMessageFlag == 1:
        errorMessage = "Your message could not be delievered to some recipients"
        senderSocket.send(errorMessage)

#function to send messages
def sendMessage(newClient, receiver, message):
    global connectionSockets
    global offlineMessages
    global blacklistedUsers

    senderSocket = connectionSockets.get(newClient.name)
    receiverSocket = connectionSockets.get(receiver)

    #prevent user from messaging themselves
    if str(receiver) == str(newClient.name):
        errorMessage = "Error: You cannot message yourself"
        senderSocket.send(errorMessage)

    #prevent user from messaging blocked user
    elif receiver in blacklistedUsers[newClient.name]:
            errorMessage = "Error: This user is blocked"
            senderSocket.send(errorMessage)

    elif newClient.name in blacklistedUsers[receiver]:
            errorMessage = "Error: This user is blocked"
            senderSocket.send(errorMessage)

    #otherwise, they can message anyone that is online
    elif receiver in connectionSockets:
        joinedMessage = "%s: " %newClient.name + " ".join(message)
        receiverSocket.send(joinedMessage)

    #if the receiver is not online but their username isvalid, store the message
    elif checkvalidUsername(receiver) == "valid":
        joinedMessage = "%s: " %newClient.name + " ".join(message)
        offlineMessages[receiver].append(joinedMessage)
        errorMessage = "Error: %s is not online. Message has been stored" %receiver
        senderSocket.send(errorMessage)

    #otherwise, check if the receiver is an actual person
    elif checkvalidUsername(receiver) == "invalid":
        errorMessage = "Error: This user does not exist"
        senderSocket.send(errorMessage)

    #bonus condition in case there is some other issue
    else:
        errorMessage = "Error: Message could not be delivered"
        senderSocket.send(errorMessage)

#function to blacklist other users
def blacklistUser(newClient, bully):
    global connectionSockets
    senderSocket = connectionSockets.get(newClient.name)

    #make sure user is not trying to block themselves
    if str(bully) == str(newClient.name):
        errorMessage = "Error: You cannot blacklist yourself"
        senderSocket.send(errorMessage)

    #if the client is valid, block communication both ways
    elif checkvalidUsername(bully) == "valid":
        blacklistedUsers[newClient.name].append(bully)    #the client can't send messages to the bully now
        blacklistedUsers[bully].append(newClient.name)    #the bully can't send messages to the client now
        Message = "%s has been blacklisted" %bully
        senderSocket.send(Message)

    #otherwise, if the client is not valid, display error message
    elif checkvalidUsername(bully) == "invalid":
        errorMessage = "Error: This user does not exist"
        senderSocket.send(errorMessage)

#function to unblock a user: similar to blacklist
def unblacklistUser(newClient, bully):
    global connectionSockets
    senderSocket = connectionSockets.get(newClient.name)

    if str(bully) == str(newClient.name):
        errorMessage = "Error: You cannot unblock yourself"
        senderSocket.send(errorMessage)

    elif bully in blacklistedUsers[newClient.name]:
        blacklistedUsers[newClient.name].remove(bully)
        blacklistedUsers[bully].remove(newClient.name)
        Message = "%s has been unblocked" %bully
        senderSocket.send(Message)

    elif checkvalidUsername(bully) == "valid":
        errorMessage = "Error: This user is not currently blocked"
        senderSocket.send(errorMessage)

    elif checkvalidUsername(bully) == "invalid":
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
    global clientList
    global timeout
    global t_lock

    newClient = client()     #create client object with each new connection

    while(1):
        try:
            #wait for username to arrive from the client
            clientUsername = connectionSocket.recv(1024)
        except:
            thread.exit()

        #if the username given is valid, break the loop and get the password
        if checkvalidUsername(clientUsername) == "valid":
            message = "valid username"
            try:
                connectionSocket.send(message)
                break
            except:
                thread.exit()
        else:
            message = "invalid username"   #otherwise if the given username is not valid, restart process
            try:
                connectionSocket.send(message)
                continue
            except:
                thread.exit()


    while(1):
        global time

        try:
            #wait for data to arrive from the client
            request = connectionSocket.recv(1024)
        except:
            thread.exit()

        clientUsername = getUsername(request)
        newClient.name = clientUsername

        if checkBlocked(clientUsername) == "blocked":   #check to see if user is currently blocked
            loginResult = "Your account is blocked due to multiple login failures. Please try again later"
            try:
                connectionSocket.send(loginResult)
                connectionSocket.close()                    #close the connectionSocket if they are blocked
            except:
                thread.exit()
        elif checkBlocked(clientUsername) == "not blocked" and newClient.name not in onlineUsers: #to log in the user, check that they're not blocked and that they're not already online
            if authenticate(request) == 1:              #if the username is not blocked, check credentials.txt to see if the username & password is valid
                onlineUsers[clientUsername] = time.time() #for the whoelse function
                loginRecord[clientUsername] = time.time() #for the whoElseSince function
                loginResult = "Authenticated"
                try:
                    connectionSocket.send(loginResult)      #if valid, send the result to the client
                except:
                    thread.exit()
                time.sleep(0.2)
                presenceBroadcast(newClient, "on")       #Someone has logged in, so send this result to everyone else online
                #send the user that just logged on, their offline messages
                if clientUsername in offlineMessages:
                    for x in offlineMessages[clientUsername]:
                        x = x + "\n"
                        connectionSocket.send(x)        #send the messages received offline to the user
                    del offlineMessages[clientUsername] #once the messages have been sent, remove the messages from storage
                
                connectionSockets[clientUsername] = connectionSocket #add the user's connection socket to the dictionary
                connectionSocket.settimeout(timeout) #set the connection socket timeout to the given value. Code syntax adpated from https://docs.python.org/2/library/socket.html

                while(1):

                    try:
                        request = connectionSocket.recv(1024)  #get data from the client
                    except:
                        #Log the user out if timeout has been reached
                        del onlineUsers[newClient.name]
                        del connectionSockets[newClient.name]
                        presenceBroadcast(newClient, "off")
                        message = "You have been logged out due to inactivity"
                        connectionSocket.send(message)
                        thread.exit()

                    with t_lock:

                        command = request.split(" ")  #parse the command sent by the client: look at the first term for the command and call the appropriate function

                        if command[0] == "logout":
                            del onlineUsers[newClient.name]
                            del connectionSockets[newClient.name]
                            presenceBroadcast(newClient, "off")
                            message = "You have been logged out"
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
                            message = command[2:]           #message is everything beyond the 2nd term
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
                if newClient.loginAttempt == 3:                         #if the client has failed 3 times, block them
                    startBlockTime = time.time()
                    blockedUsers[clientUsername] = startBlockTime
                    loginResult = "Invalid Password. Your account has been blocked. Please try again later"
                    connectionSocket.send(loginResult)
                    connectionSocket.close()   #close the connectionSocket. Note that the serverSocket is still alive waiting for new clients
                    thread.exit()
                else:
                    loginResult = "Invalid Password. Please try again"
                    try:
                        connectionSocket.send(loginResult)
                    except:
                        thread.exit()
        else:
            alreadyOnline = "That user is already logged in"
            try:
                connectionSocket.send(alreadyOnline)
                thread.exit()
            except:
                thread.exit()


#################################################### MAIN SECTION ####################################################################################

fillvalidUsernames()  #fill the validUsernames list using credentails.txt

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

    #accept connection
    connectionSocket, addr = sock.accept()

    # Start a new thread and return its identifier for each new connection
    thread.start_new_thread(recv_handler, (connectionSocket, )) 





