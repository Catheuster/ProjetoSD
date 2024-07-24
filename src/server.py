import socket
import struct
import threading

#definindo o endereço IP do host
MANAGER_HOST = "localhost"
#definindo o número da porta em que o servidor irá escutar pelas requisições HTTP
MANAGER_PORT = 8080

protocolo = {
    "FAIL" : "0 REQUEST FAIL\n",
    "REGISTRATION" : "1 SERVER CLAIM\n",
    "GOOD" : "2 REQUEST SUCCESS\n",
    "REPL": "3 REPLICATE REQUEST\n"
}
class ServerUnit:

    capacidadeAtual = 0
    port = None
    sock = None
    pathToOwnedFolder = None

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


    def replicate(self,data,servidor):
        pass

    def lsCall(self,connection):
        pass

    def fail(self):
        pass

    def requestHandler(self, client_connection, client_adress):
        pass

    def makeListen(self):
        pass
def main():
    #SETUP AT LEAST 4 SERVER UNITS
    pass