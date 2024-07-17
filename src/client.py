import socket
import struct
import os

credencial_g = None
SERVER_HOST_g = "localhost"
SERVER_PORT_g = 8080

protocolo = {
    "QANS" : "0 Question Answer",
    "LOGIN" : "1 Login Request\n",
    "ASKREQ" : "2 Request for File\n",
    "PUSH" : "3 Push File Warning\n",
    "LS": "4 ls Request\n",
    "LOGOUT": "5 Logout Warning",
}

def pushData(connection):
    global credencial_g
    controlMessage = "Percorra o sistema de arquivos e selecione o que se deseja transferir utilizando os seguintes comandos:\nm-[NOME DO DIRETORIO] para mover de diretório.;\ns-[NOME DO ARQUIVO] para selecionar o arquivo para transferir\nc-[NADA] para cancelar a operação"
    currDirectory = os.path.expanduser("~")
    showcontrol = True
    arquivo = None
    #Selecting
    while (arquivo==None):
        if (showcontrol):
            print(controlMessage)
            try:
                root, dirs, files = next(os.walk(currDirectory))
                dirs = [d for d in dirs if not d[0]=='.']
                files = [f for f in files if not f[0]=='.']
            except:
                print("Diretório invalido, cancelando operação")
                break
            print ("Diretório atual: "+root)
            print ("Diretórios filhos: ")
            print (*dirs,sep=" ",end="\n\n")
            print ("Arquivos do diretório atual:")
            print (*files,sep=" ",end="\n\n")
        cmd = input("Escolha o comando: ")
        errmsg = "cmd vazio"
        try:
            if (cmd[0]=='m'):
                currDirectory = os.path.join(currDirectory,cmd[2:])
            elif (cmd[0]=='s'):
                arqPath = os.path.join(currDirectory,cmd[2:])
                errmsg="arquivo selecionado inexistente"
                f = open(arqPath,"r")
                arquivo = (f.read(),cmd[2:])
                f.close()
            elif (cmd[0]=='c'):
                break
            else:
                print("Comando inválido")
        except:
            print(errmsg)
    #works up to here
    #TODO send

    if(arquivo != None):
        data, nome = arquivo
        warnPush = protocolo["PUSH"]+credencial_g+"\n"+nome
        towrite = True
        #connection.sendall(warnPush.encode)
        #1 já existe 0 nao existe
        if (connection.recv(1028).decode()[0]==1):
            ans = input("Deseja sobre escrever no destino?[Y/n]: ")
            if (ans!="Y" and ans!="y"): towrite=False
            ans = protocolo["QANS"]+credencial_g+"\n"+ans
            connection.sendall(ans)
        if (towrite):
            pass
            #Figure this shit out


def pullArquivo(connection):
    global credencial_g
    arq = input("Escreva o nome e a extensão do arquivo que se deseja: ")
    msg = protocolo["ASKREQ"]+credencial_g+"\n"+arq
    #connection.sendall(msg.encode())
    #TODO recieve

def lsCall(connection):
    global credencial_g
    msg = protocolo["LS"]+credencial_g+"\n"
    #connection.sendall(msg.encode())
    #TODO recieve

def login(connection,credencial):
    global credencial_g
    msg = protocolo["LOGIN"]+credencial_g+"\n"
    #connection.sendall(msg.encode())

def logout(connection):
    global credencial_g
    msg = protocolo["LOGOUT"]+credencial_g+"\n"
    #connection.sendall(msg.encode())

def controlMain():
    maintainFunc = True
    showCommands = True
    global credencial_g
    credencial_g = str(input("Entre sua identificação de usuario: "))
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
                print("Envie 1 para enviar")
                print("Envie 2 para buscar")
                print("Envie 3 para ls")
                print("Envie 4 para terminar")
                showCommands = False
            command = int(input("Escolha comando: "))
            #f-this
            showCommands=True
            if (command==0):
                print(connectionSocket.recv(1028).decode()) #test code
            elif (command==1):
                pushData(connectionSocket)
            elif (command==2):
                pullArquivo(connectionSocket)
            elif (command==3):
                pass
            elif (command==4):
                logout(connectionSocket)
                maintainFunc=False
            else:
                print("Comando não reconhecido")
                showCommands=False
        except:
            maintainFunc = False
    
    connectionSocket.close()
    print("control end")
    return 0

if __name__=="__main__":
    controlMain()