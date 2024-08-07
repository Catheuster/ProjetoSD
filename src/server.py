import socket
import os
import threading
import tempfile
import struct

#definindo o endereço IP do host
MANAGER_HOST = "localhost"
#definindo o número da porta em que o servidor irá escutar pelas requisições HTTP
MANAGER_PORT = 2525

protocolo = {
    "FAIL" : "0 REQUEST FAIL\n",
    "REGISTRATION" : "1 SERVER CLAIM\n",
    "GOOD" : "2 REQUEST SUCCESS\n",
    "READY": "8 READY\n",
    "REPL": "9 REPLICATE REQUEST\n"
}

class ServerUnit:

    capacidadeAtual = 0
    port = None
    sock = None
    pathToOwnedFolder = None
    I_listen = False

    def __init__(self,folderNumber):
        global MANAGER_HOST
        global MANAGER_PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 0))
        self.port = self.sock.getsockname()[1]
        #making folder
        parent = os.path.join(os.getcwd(),"VirtualServers")
        self.pathToOwnedFolder = os.path.join(parent,str(folderNumber))
        if not os.path.isdir(self.pathToOwnedFolder):
            os.mkdir(self.pathToOwnedFolder)
        giveUP = False
        try:
            registrationSocket = socket.create_connection((MANAGER_HOST, MANAGER_PORT))
            print("connection success")
        except:
            print("connection failed")
            giveUP = True
            self.fail()

        if not giveUP:
            message = protocolo["REGISTRATION"]+str(self.port)
            #following should be in try catch
            registrationSocket.sendall(message.encode())
            didIdoit = int(registrationSocket.recv(2048).decode().split('\n')[0][0])
            if didIdoit!=1:
                self.fail()
                
            registrationSocket.close()

    def takeData(self,connection,user,fileName):
        #making file
        insideLoc = os.path.join(self.pathToOwnedFolder,user)
        if (not os.path.isdir(insideLoc)):
            os.mkdir(insideLoc)
        abspath = os.path.join(insideLoc,fileName)
        try :
            with open(abspath,"wb") as f:
                #I confirm intent do take
                msg = protocolo["READY"]
                connection.sendall(msg.encode())
                #bla = connection.recv(struct.calcsize("<Q"))
                #print(struct.unpack("<Q",bla))
                ullSize = struct.unpack("<Q",connection.recv(struct.calcsize("<Q")))[0]
                connection.sendall(msg.encode())
                data = bytes()
                now = 0
                while now < ullSize:
                    chunk = connection.recv(2048)
                    now += len(chunk)
                    data += chunk
                f.write(data)
        except Exception as e:
            print("takedata failure")
            print(repr(e))
        pass

    def sendFile(self,connection,filePath):
        #should be guarded, no none filePath
        if os.path.exists(filePath) and not os.path.isdir(filePath):
            #just in case
            #connected should be already warned and waiting for file size
            ulliSize = os.path.getsize(filePath)
            print(ulliSize)
            connection.sendall(struct.pack("<Q",ulliSize))
            #get confirmed
            conf = connection.recv(2048).decode()
            if int(conf[0]) == 8:
                #alright send data
                with open(filePath,"rb") as data:
                    connection.sendall(data.read())
            else:
                print("failure, no confirmation after sendFile size")
        else:
            print("send file but no file")
            #fail message
            zero = 0
            connection.sendall(struct.pack("<Q",zero))

    def replicate(self,usr,fileName,secdnServ):
        #when called, should have already taken
        f = self.fetch(usr,fileName)
        if f:
            #connect only and call sendFile
            doit = True
            try:
                #localhost vibes go so local
                connectionSocket = socket.create_connection(("localhost",secdnServ))
            except:
                print("connection failed at serverxserver replicate")
                doit = False
            if doit:
                hello = protocolo["REPL"]+usr+"\n"+fileName
                connectionSocket.sendall(hello.encode())
                conf = connectionSocket.recv(2048).decode()
                if int(conf[0])==8:
                    self.sendFile(connectionSocket,f)
            #then dc
            connectionSocket.close()
        else:
            print("replicate called but no file")
        pass

    def askForFile(self,connection,usr,fileName):
        f = self.fetch(usr,fileName)
        if f:
            message = protocolo["GOOD"]
            connection.sendall(message.encode())
            action = connection.recv(2048).decode()
            print(action)
            if (int(action[0])==8):
                self.sendFile(connection,f)
                pass
            elif (int(action[0])==6):
                os.remove(f)
            #else, do nothing
        else:
            message = protocolo["FAIL"]
            connection.sendall(message.encode())

    def delete(self,usr,fileName):
        usrfile = self.fetch(usr,fileName)
        if usrfile:
            os.remove(usrfile)

    def fetch(self,usr,fileName):
        usrfile = os.path.join(usr,fileName)
        completePath = os.path.join(self.pathToOwnedFolder,usrfile)
        if (os.path.exists(completePath)):
            return completePath
        return None

    def lsCall(self,connection,user):
        usrDir = os.path.join(self.pathToOwnedFolder,user)
        if os.path.isdir(usrDir):
            msg = protocolo["GOOD"]
            connection.sendall(msg.encode())
            _, _, files = next(os.walk(usrDir))
            tmpf = tempfile.NamedTemporaryFile(mode="w",delete=False) #already in binary mode
            location = tmpf.name
            tmpf.write(",".join(files))
            tmpf.close()
            ans = connection.recv(2048).decode()
            if int(ans[0])==8:
                self.sendFile(connection, location)
            os.remove(location)
            #should have only files as we do not have make dir functionality
        else:
            #print("no folder of user")
            message = protocolo["FAIL"]
            connection.sendall(message.encode())

    def fail(self):
        if self.sock:
            print("shutting server down of port",self.port)
            self.sock.close() #may have other things
        self.sock = None

    def requestHandler(self, connection, address):
        request = connection.recv(2048).decode().split("\n")
        print(repr(request))
        try:
            #why you calling me?
            op = int(request[0][0])
            user = request[1]
            match op:
                case 9:
                    #oh a replicate request, alright
                    #overwrite always true in replicate
                    fileName = request[2]
                    self.takeData(connection,user,fileName)
                case 2:
                    fileName = request[2]
                    self.askForFile(connection,user,fileName)
                case 3:
                    self.lsCall(connection,user)
                case 4:
                    fileName = request[2]
                    otherServPort = request[3]
                    self.takeData(connection,user,fileName)
                    self.replicate(user,fileName,int(otherServPort))
        except Exception as e:
            print(repr(e))
        connection.close()


    def listening(self):
        self.sock.listen(1)
        self.I_listen=True
        if self.sock:
            try:
                while self.I_listen:
                    connection, address = self.sock.accept()
                    connection.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
                    client_thread = threading.Thread(target=self.requestHandler, args=(connection, address),
                                                    daemon=True)
                    client_thread.start()
            finally:
                self.fail()

    def startListen(self):
        hear = threading.Thread(target=self.listening,daemon=True)
        hear.start()
    
def main():
    servers = []
    for i in range(4):
        servers.append(ServerUnit(i))
    for unit in servers:
        unit.startListen()
    input("press anything to kill them all")
    for unit in servers:
        unit.fail()
    
if __name__=="__main__":
    main()
