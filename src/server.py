import socket
import os
import threading
import tempfile

#definindo o endereço IP do host
MANAGER_HOST = "localhost"
#definindo o número da porta em que o servidor irá escutar pelas requisições HTTP
MANAGER_PORT = 8080

protocolo = {
    "FAIL" : "0 REQUEST FAIL\n",
    "REGISTRATION" : "1 SERVER CLAIM\n",
    "GOOD" : "2 REQUEST SUCCESS, SEND WARNING\n",
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
        giveUP = False
        try:
            registrationSocket = socket.create_connection((MANAGER_HOST, MANAGER_PORT))
            print("connection success")
        except:
            print("connection failed")
            giveUP = True
            self.fail()

        if not giveUP:
            message = protocolo["REGISTRATION"]+self.port
            registrationSocket.sendall(message.encode())
            didIdoit = int(registrationSocket.recv(2048).decode().split('\n')[0][0])
            if didIdoit==0:
                self.fail()
            else:
                #TODO SETUP LISTEN RIGHT, SETUP FOLDER
                pass
        registrationSocket.close()

    def takeData(self,connection,user):
        #TODO figure this shi out
        pass
    def replicate(self,data,portServ):
        pass

    def sendFile(self,connection,file):
        message = protocolo["GOOD"]
        connection.sendall(message)
        #TODO Figure this shi out

    def upRequest(self,connection,usr,file):
        pass

    def fetch(self,connection,usr,file):
        pass
    def lsCall(self,connection,user):
        usrDir = os.path.join(self.pathToOwnedFolder,user)
        try:
            root, dirs, files = (os.walk(usrDir))
            #TODO make text file and send over
            tmpf = tempfile.TemporaryFile() #already in binary mode
            tmpf.write(("\n".join(files)).encode())
            self.sendFile(connection, tmpf)
            tmpf.close() #immediatly kills it
            #should have only files as we do not have make dir functionality
        except:
            print("no folder of user")
            message = protocolo["FAIL"]
            connection.sendall(message.encode())

    def fail(self):
        self.sock.close() #may have other things

    def requestHandler(self, connection, address):
        request = connection.recv(2048).decode().split("\n")
        try:
            #why you calling me?
            op = int(request[0][0])
            user = request[1]
            match op:
                case 9:
                    #oh a replicate request, alright
                    #overwrite always true in replicate
                    self.takeData(connection,user)
                case 2:
                    fileName = request[2]
                    self.fetch(connection,user,fileName)
                case 3:
                    self.lsCall(connection,user)
                case 4:
                    fileName = request[2]
                    self.upRequest(connection,user,fileName)
        except:
            print("malformed request")
        connection.close()


    def makeListen(self):
        self.I_listen=True
        try:
            while self.I_listen:
                # espera por conexões
                # client_connection: o socket que será criado para trocar dados com o cliente de forma dedicada
                # client_address: tupla (IP do cliente, Porta do cliente)
                connection, address = self.sock.accept()
                client_thread = threading.Thread(target=self.requestHandler, args=(connection, address),
                                                 daemon=True)
                client_thread.start()
        finally:
            self.fail()
def main():
    #SETUP AT LEAST 4 SERVER UNITS
    pass