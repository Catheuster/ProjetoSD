import threading
import socket
import struct

#definindo o endereço IP do host
SERVER_HOST = ""
#definindo o número da porta em que o servidor irá escutar pelas requisições HTTP
SERVER_PORT = 8080

usrConectados_g: dict = {}
serverConectados_g: dict = {}

def requestHandler(client_connection, client_adress):
    # verifica se a request possui algum conteúdo (pois alguns navegadores ficam periodicamente enviando alguma string vazia)
    clienteAtual = None
    # pega a solicitação do cliente
    request = None
    if request:
        # imprime a solicitação do cliente
        # print(request)

        # analisa a solicitação HTTP
        headers = request.split("\n")
        # pega o nome do arquivo sendo solicitado
        filename = headers[0].split()[1]
        requestType = headers[0].split()[0]
        # verifica qual arquivo está sendo solicitado e envia a resposta para o cliente

        # envia a resposta
        response = "DEFAULT RESPONSE"
        client_connection.sendall(response.encode())
        #client_connection.close() #close only when logout

def broadcastReq(cliente,arquivo):
    pass

def targetPost(data,serverFirst,serverRepl):
    pass

def targetPullBroadcast(cliente,arquivo):
    pass

def targetDecide():
    pass

def userLogin(credencial, connection):
    #TODO send login confirm
    return credencial

def userLogout(credencial,connection):
    #TODO send logout confirm
    connection.close()

def recieveBody(connection,address):
    pass

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # vamos setar a opção de reutilizar sockets já abertos
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # atrela o socket ao endereço da máquina e ao número de porta definido
    server_socket.bind((SERVER_HOST, SERVER_PORT))

    # coloca o socket para escutar por conexões
    server_socket.listen(1)

    # mensagem inicial do servidor
    print("Servidor em execução...")
    print("Escutando por conexões na porta %s" % SERVER_PORT)

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
