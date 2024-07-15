import socket
import struct

credencial_g = None
SERVER_HOST_g = "localhost"
SERVER_PORT_g = 8080

def pushData(connection,data):
    pass

def pullArquivo(connection,arquivo):
    pass

def lsCall(connection):
    pass

def login(connection,credencial):
    pass

def logout(connection):
    pass

def controlMain():
    maintainFunc = True
    showCommands = True
    credencial_g = input("Entre sua identificação de usuario: ")
    connectionSocket = None
    try:
        connectionSocket = socket.create_connection((SERVER_HOST_g,SERVER_PORT_g))
        login(connectionSocket,credencial_g)
        print("connection success")
    except:
        print("connection failed")
        maintainFunc = False

    while (maintainFunc):
        try:
            if (showCommands):
                print("Envie 0 para receber")
                print("Envie 2 para enviar")
                print("Envie 3 para buscar")
                print("Envie 4 para ls")
                print("Envie 5 para terminar")
                showCommands = False
            command = int(input("Escolha comando: "))
            #f-this
            showCommands=True
            if (command==1):
                print(connectionSocket.recv(1028).decode()) #test code
            elif (command==2):
                pass
            elif (command==3):
                pass
            elif (command==4):
                pass
            elif (command==5):
                maintainFunc=False
            else:
                print("Comando não reconhecido")
                showCommands=False
        except:
            connectionSocket.close()
            maintainFunc = False

    print("control end")
    return 0

if __name__=="__main__":
    controlMain()