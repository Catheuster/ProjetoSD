import socket
import struct
import os
import tempfile

credencial_g = None
SERVER_HOST_g = "localhost"
SERVER_PORT_g = 8080

protocolo = {
    "FAIL" : "0 FAILURE\n",
    "LOGIN" : "1 Login Request\n",
    "ASKREQ" : "2 Request for File\n",
    "PUSH" : "3 Push File Request\n",
    "LS": "4 LS Request\n",
    "LOGOUT": "5 Logout Warning\n",
    "READY": "8 Ready to Recieve"
}

def pushData(connection):
    global credencial_g
    controlMessage = "Percorra o sistema de arquivos e selecione o que se deseja transferir utilizando os seguintes comandos:\nm-[NOME DO DIRETORIO] para mover de diretório.;\ns-[NOME DO ARQUIVO] para selecionar o arquivo para transferir\nc-[NADA] para cancelar a operação"
    currDirectory = os.path.expanduser("~")
    showcontrol = True
    arqPath = None
    #Selecting
    while (arqPath==None):
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
        try:
            if (cmd[0]=='m'):
                currDirectory = os.path.join(currDirectory,cmd[2:])
            elif (cmd[0]=='s'):
                arqPath = os.path.join(currDirectory,cmd[2:])
                fileName = cmd[2:]
                if not os.path.exists(arqPath):
                    print("file apontada inexistente\ncancelando operação\n\n")
                    arqPath=None
            elif (cmd[0]=='c'):
                break
            else:
                print("Comando inválido")
        except:
            print("cmd vazio")
    #works up to here
    #TODO send
    if arqPath:
        trySend(connection,arqPath,fileName)
    

def trySend(connection,path,filename):
    global credencial_g
    msg = protocolo["PUSH"]+credencial_g+"\n"+filename
    connection.sendall(msg.encode())
    ans = connection.recv(2048).decode()
    print(ans)
    doit = True
    if int(ans[0]) == 8:
        yn = input("File already in server, wish to overwrite?[Y/n]: ")
        if yn =="Y" or yn=="y":
            connection.sendall(msg.encode()) #sending push again, I don't like putting it here  
        else:
            doit = False
            print("canceling operation")
            
    if int(ans[0]) == 0:
        print("manager killed itself")
        doit=False
        return #stop it now
    
    if doit:
        going = int(connection.recv(2048).decode()[0])
        if going == 7:
            sendFile(connection,path)
        else:
            print("manager didn't confirm to start recv")
    else:
        msg = protocolo["FAIL"]+credencial_g+"\n"
        #this is gonna m
        connection.sendall(msg.encode())
        conf = connection.recv(2048) #important to happen, can be used to check


def sendFile(connection,filePath):
        #should be guarded, no none filePath
        if filePath:
            #just in case
            #connected should be already warned and waiting for file size
            ulliSize = os.path.getsize(filePath)
            print(ulliSize)
            bla = struct.pack("<Q",ulliSize)
            ble = struct.unpack("<Q",bla)
            print(ble)
            print(struct.calcsize("<Q"))
            print(len(bla))
            connection.sendall(struct.pack("<Q",ulliSize))
            #get confirmed
            conf = connection.recv(2048).decode()
            if int(conf[0]) == 7:
                #alright send data
                with open(filePath,"rb") as data:
                    connection.sendall(data.read())
            else:
                print("failure, no confirmation after sendFile size")

def pullArquivo(connection):
    global credencial_g
    arqName = input("Escreva o nome do arquivo que se deseja: ")
    msg = protocolo["ASKREQ"]+credencial_g+"\n"+arqName
    connection.sendall(msg.encode())
    ans = connection.recv(2048).decode()
    if int(ans[0])!=0:
        f = tempfile.NamedTemporaryFile(delete=False)
        location = f.name
        f.close()
        takeFile(connection,location)

        controlMessage = "Percorra o sistema de arquivos e selecione o diretório para o qual se deseja transferir utilizando os seguintes comandos:\nm-[NOME DO DIRETÓRIO] para mover de diretório.;\ns-[NOME DO DIRETÓRIO] para selecionar o arquivo para transferir\n"
        currDirectory = os.path.expanduser("~")
        showcontrol = True
        dirPath = None
        #Selecting
        while (dirPath==None):
            if (showcontrol):
                print(controlMessage)
                try:
                    root, dirs, _ = next(os.walk(currDirectory))
                    dirs = [d for d in dirs if not d[0]=='.']
                except:
                    print("Diretório invalido, cancelando operação")
                    break
                print ("Diretório atual: "+root)
                print ("Diretórios filhos: ")
                print (*dirs,sep=" ",end="\n\n")
            cmd = input("Escolha o comando: ")
            try:
                if (cmd[0]=='m'):
                    currDirectory = os.path.join(currDirectory,cmd[2:])
                elif (cmd[0]=='s'):
                    dirPath = os.path.join(currDirectory,cmd[2:])
                    if not os.path.isdir(dirPath):
                        print("diretório inexistente")
                        dirPath=None
                else:
                    print("Comando inválido")
            except:
                print("cmd vazio")
        #alright I have the dir
        finalfile = os.path.join(dirPath,arqName)
        print(finalfile)
        with open(finalfile,"wb") as ff:
            print("error was not final file")
            tmp = open(location,"rb")
            ff.write(tmp.read())
            tmp.close()
            ff.close()
        os.remove(location)
    print("donwload completo")

def takeFile(connection,pathToTmp):
    
    try :
        with open(pathToTmp,"wb") as f:
            #I confirm intent do take
            msg = protocolo["READY"]
            connection.sendall(msg.encode())
            ullSize = struct.unpack("<Q",connection.recv(struct.calcsize("<Q")))[0]
            connection.sendall(msg.encode())
            data = bytes()
            now = 0
            while now < ullSize:
                chunk = connection.recv(2048)
                now += len(chunk)
                data += chunk
            f.write(data)
    except:
        print("takedata failure")

def lsCall(connection):
    global credencial_g
    msg = protocolo["LS"]+credencial_g+"\n"
    connection.sendall(msg.encode())
    #TODO recieve

def login(connection,credencial):
    global credencial_g
    msg = protocolo["LOGIN"]+credencial_g+"\n"
    connection.sendall(msg.encode())

def logout(connection):
    global credencial_g
    msg = protocolo["LOGOUT"]+credencial_g+"\n"
    connection.sendall(msg.encode())

def controlMain():
    maintainFunc = True
    showCommands = True
    global credencial_g
    credencial_g = str(input("Entre sua identificação de usuario: "))
    connectionSocket = None
    try:
        connectionSocket = socket.create_connection((SERVER_HOST_g,SERVER_PORT_g))
        connectionSocket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
        login(connectionSocket,credencial_g)
        conf = connectionSocket.recv(2048).decode()
        if int(conf[0])==0:
            raise
        print("connection success")
    except:
        print("connection failed")
        maintainFunc = False

    while (maintainFunc):
        try:
            if (showCommands):
                print("Envie 1 para enviar")
                print("Envie 2 para buscar")
                print("Envie 3 para ls")
                print("Envie 4 para terminar")
                showCommands = False
            command = int(input("Escolha comando: "))
            #f-this
            showCommands=True
            if (command==1):
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
        except Exception as e:
            maintainFunc = False
            print(repr(e))
    
    connectionSocket.close()
    print("control end")
    return 0

if __name__=="__main__":
    controlMain()