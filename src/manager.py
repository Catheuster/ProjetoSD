import threading
import socket
import struct

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
    "NOSERV" : "9 NO SERVERS\n"
}

protocoloServer = {
    "FAIL" : "0 FAILURE\n",
    "REGWIN": "1 REGISTRATION SUCCESS\n",
    "REQFILE": "2 REQUEST FILE\n",
    "REQLS": "3 REQUEST LS\n",
    "UPR": "4 UPLOAD REQUEST\n",
    "UPW": "5 UPLOAD WARNING\n"
}

def requestHandler(client_connection, client_adress):
    global serverConectados_g
    clienteAtual = None
    while True:
        # verifica se a request possui algum conteúdo (pois alguns navegadores ficam periodicamente enviando alguma string vazia)

        # pega a solicitação do cliente inicial de comunicação
        request = client_connection.recv(2048)
        if request:
            headers = request.split("\n")
            user = headers[1]
            body = headers[2]
            op = int(headers[0][0])
            if not serverConectados_g:
                message = protocoloCliente["NOSERV"]
                client_connection.sendall(message.encode())
            if not clienteAtual:
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
                    case 2:
                        #TODO Ask file
                        broadcastReq(client_connection,clienteAtual,body)
                        pass
                    case 3:
                        #TODO Post file
                        recieveFileToPush(client_connection,clienteAtual,body)
                        pass
                    case 4:
                        #TODO LS
                        pass
                    case 5:
                        break
        else:
            break
        client_connection.close()

def broadcastReq(connectionClient,cliente,arquivo):
    pass

def broadcastLS(connection,cliente):
    pass
def targetPost(data,serverFirst,serverRepl):
    pass

def targetPullBroadcast(cliente,arquivo):
    pass

def targetDecide():
    pass

def userLogin(credencial, connection):
    #TODO send login confirm
    message = protocoloCliente["LOGIN"]+credencial
    connection.sendall(message.encode())
    return credencial

def userLogout(credencial,connection):
    #NOT NEEDED
    pass

def recieveFileToPush(connection,user,fileName):
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
            message = (server_connection.recv(1028).decode()).split("\n")
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