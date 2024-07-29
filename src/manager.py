import threading
import socket
import struct
import os
import tempfile

#definindo o endereço IP do host
SERVER_HOST = ""
#definindo o número da porta em que o servidor irá escutar pelas requisições HTTP
SERVER_PORT_CLIENT = 8080
SERVER_PORT_MAN = 2525

serverConectados_g = []

protocoloCliente = {
    "FAIL" : "0 FAILURE\n",
    "LOGIN" : "1 LOGIN SUCCESS\n",
    "PWIN" : "2 PULL SUCCESS\n",
    "UWIN" : "3 WIN SUCCESS\n",
    "QWIN" : "4 LS QUERY SUCCESS\n",
    "LOGOUT" : "5 LOGOUT SUCCESS\n",
    "READY": "7 READY",
    "OVERWRITE": "8 OVERWRITE QUESTION\n",
    "NOSERV" : "9 NO SERVERS\n"
}

protocoloServer = {
    "FAIL" : "0 FAILURE\n",
    "REGWIN": "1 REGISTRATION SUCCESS\n",
    "REQFILE": "2 REQUEST FILE\n",
    "REQLS": "3 REQUEST LS\n",
    "UPR": "4 UPLOAD WARNING\n",
    "BRING": "5 SEND OVER\n",
    "DELETE": "6 KILL IT\n",
    "READY": "8 READY\n",
    "CAUSE REPLICATE": "9 REPLICATE\n"
}
# caso CAUSE REPLICATE 9 é só para ser usado se un número insuficiente de servidores responderam a uma 2 REQUEST FILE

def requestHandler(client_connection, client_adress):
    global serverConectados_g
    clienteAtual = None
    while True:
        # verifica se a request possui algum conteúdo (pois alguns navegadores ficam periodicamente enviando alguma string vazia)

        # pega a solicitação do cliente inicial de comunicação
        request = client_connection.recv(2048).decode()
        if request:
            headers = request.split("\n")
            user = headers[1]
            body = headers[2]
            op = int(headers[0][0])
            if not serverConectados_g:
                message = protocoloCliente["NOSERV"]
                client_connection.sendall(message.encode())
            elif not clienteAtual:
                if op == 1:
                    clienteAtual = userLogin(user,client_connection)
                else:
                    continue
            else:
                match op:
                    case 1:
                        #TODO logged in response
                        message=protocoloCliente["LOGIN"]+clienteAtual
                        client_connection.sendall(message.encode())
                        pass
                    case 2:
                        #TODO Ask file
                        broadcastReq(client_connection,clienteAtual,body,mode=0)
                        pass
                    case 3:
                        #TODO Post file
                        broadcastReq(client_connection,clienteAtual,body,mode=1)
                        pass
                    case 4:
                        #TODO LS
                        pass
                    case 5:
                        break
        else:
            break
    client_connection.close()

def broadcastReq(connectionClient,cliente,fileName,mode=0):
    #mode 0 when just pulling, mode 1 when pushing
    #temporary to test
    global serverConectados_g
    hitlist = []
    for serv in serverConectados_g:
        try:
            sock = socket.create_connection(serv)
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
            msg = protocoloServer["REQFILE"]+cliente+"\n"+fileName
            sock.sendall(msg.encode())
            ans = (sock.recv(2048)).decode()
            if (int(ans[0])==2):
                hitlist.append(sock)
            else:
                sock.close()
        except Exception as e:
            print("failure at broadcast req server connect")
            print(repr(e))
    match mode:
        case 1:
            #pushing
            if hitlist:
                #ask overwrite
                msgC = protocoloCliente["OVERWRITE"]
                connectionClient.sendall(msgC.encode())
                ans = (connectionClient.recv(2048)).decode()
                if int(ans[0]) == 3:
                    for sk in hitlist:
                        msgS = protocoloServer["DELETE"]
                        sk.sendall(msgS.encode())
                        sk.close()
                    takeAndSpread(connectionClient,cliente,fileName)
                else:
                    for sk in hitlist:
                        msgS = protocoloServer["FAIL"]
                        sk.sendall(msgS.encode())
                        sk.close()
            else:
                takeAndSpread(connectionClient,cliente,fileName)
        case 0:
            #pulling
            if hitlist:
                #close others
                msg = protocoloServer["FAIL"]
                for sk in hitlist[1:]:
                    sk.sendall(msg.encode())
                    sk.close()
                pullAndReturn(connectionClient,hitlist[0])
            else:
                msg = protocoloCliente["FAIL"]
                connectionClient.sendall(msg.encode())
    
def takeAndSpread(sockC,cliente,filename):
    tf = tempfile.NamedTemporaryFile(delete=False)
    location = tf.name
    try :
        #I confirm intent do take
        msg = protocoloCliente["READY"]
        sockC.sendall(msg.encode())
        ullSize = struct.unpack("<Q",sockC.recv(struct.calcsize("<Q")))[0]
        sockC.sendall(msg.encode())
        data = bytes()
        now = 0
        while now < ullSize:
            chunk = sockC.recv(2048)
            now += len(chunk)
            data += chunk
        tf.write(data)
    except Exception as e:
        print("takedata failure")
        print(repr(e))
    finally:
        tf.close()
    targetList = targetDecide()
    targetPost(location,cliente,filename,targetList[0],targetList[1:])
    
    os.remove(location)

def pullAndReturn(sockC,sockS):
    msg = protocoloServer["BRING"]
    sockS.sendall(msg.encode())
    ulliSize = struct.unpack("<Q",sockS.recv(struct.calcsize("<Q")))[0]
    msg = protocoloServer["READY"]
    sockS.sendall(msg.encode())
    data = bytes()
    now = 0
    while now < ulliSize:
        chunk = sockS.recv(2048)
        now += len(chunk)
        data += chunk

    msg = protocoloCliente["PWIN"]
    sockC.sendall(msg.encode())
    conf = (sockC.recv(2048)).decode()
    if int(conf[0])!=0:
        sockC.sendall(struct.pack("<Q",ulliSize))
        #get confirmed
        conf = (sockC.recv(2048)).decode()
        if int(conf[0]) == 8:
            #alright send data
            sockC.sendall(data)
            print("I sent")
        else:
            print("failure, no confirmation after sendFile size")

def broadcastLS(connection,cliente):
    pass

def targetPost(filepath,cliente,filename,serverFirst,serverRepl):
    #assume servers are responding
    global serverConectados_g
    ports = []
    for i in serverRepl:
        ports.append(str(serverConectados_g[i][1]))
        
    msg = protocoloServer["UPR"]+cliente+"\n"+filename+"\n"+(",".join(ports))
    try:
        sock = socket.create_connection(serverConectados_g[serverFirst])
    except:
        print("failure at target post connect")
        return #screw this
    sock.sendall(msg.encode())
    ans = (sock.recv(2048)).decode()
    if int(ans[0])==8:
        ulliSize = os.path.getsize(filepath)
        sock.sendall(struct.pack("<Q",ulliSize))
        #get confirmed
        conf = (sock.recv(2048)).decode()
        if int(conf[0]) == 8:
            #alright send data
            with open(filepath,"rb") as data:
                sock.sendall(data.read())
        else:
            print("failure, no confirmation after sendFile size")
    else :
        print("failure at target post")


def targetDecide():
    return [0,1]

def userLogin(credencial, connection):
    #TODO send login confirm
    message = protocoloCliente["LOGIN"]+credencial+" ass"
    connection.sendall(message.encode())
    return credencial

def userLogout(credencial,connection):
    #NOT NEEDED
    pass

def listenClients():
    global SERVER_PORT_CLIENT
    global SERVER_HOST
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT_CLIENT))
    server_socket.listen(1)

    # mensagem inicial do servidor
    print("Servidor escutando clientes...")
    print("Escutando por conexões na porta %s" % SERVER_PORT_CLIENT)

    # cria o while que irá receber as conexões
    try:
        while True:
            # espera por conexões
            # client_connection: o socket que será criado para trocar dados com o cliente de forma dedicada
            # client_address: tupla (IP do cliente, Porta do cliente)
            client_connection, client_address = server_socket.accept()
            client_connection.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
            client_thread = threading.Thread(target=requestHandler, args=(client_connection, client_address),
                                             daemon=True)
            client_thread.start()
    finally:
        server_socket.close()

def listenServers():
    global SERVER_HOST
    global SERVER_PORT_MAN
    global serverConectados_g
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT_MAN))
    server_socket.listen(1)

    # mensagem inicial do servidor
    print("Servidor escudando servidores...")
    print("Escutando por conexões na porta %s" % SERVER_PORT_MAN)

    # cria o while que irá receber as conexões
    try:
        while True:
            server_connection, server_address = server_socket.accept()
            message = ((server_connection.recv(2048)).decode()).split("\n")
            try:
                if int(message[0][0]) == 1:
                    serverWorkingAddress = (server_address[0],int(message[1]))
                    print("registered server of port", serverWorkingAddress[1])
                    serverConectados_g.append(serverWorkingAddress)
                    message = protocoloServer["REGWIN"]
                    server_connection.sendall(message.encode())
            except:
                print("poorly written registration")
            
    finally:
        server_socket.close()

def main():
    client_man_thread = threading.Thread(target=listenClients, daemon=True)
    server_man_thread = threading.Thread(target=listenServers, daemon=True)
    client_man_thread.start()
    server_man_thread.start()
    client_man_thread.join()
    server_man_thread.join()

if __name__=="__main__":
    main()