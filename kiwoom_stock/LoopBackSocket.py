import socket
import pickle
import numpy as np

HOST = '127.0.0.1'
PORT = 7000

class ServerSocket():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

        self.socket.bind((HOST,PORT))
        self.socket.listen()

    def AcceptWait(self):
        self.client_socket, self.client_addr = self.socket.accept()
        print("Accept complete")


    def Waiting(self):
       
        data_ = self.client_socket.recv(100000)
        if data_:
            data = pickle.loads(data_)
            # print("From client")
            # print(data)
            return data

    def SendData(self, input):
        data = pickle.dumps(input)
        self.client_socket.sendall(data)




class ClientSocket():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.socket.connect((HOST,PORT))


    def Waiting(self):
       
        data_ = self.socket.recv(100000)
        if data_:
            data = pickle.loads(data_)
            # print("From server:")
            # print(data)
            return data

    def SendData(self, input):
        data = pickle.dumps(input)
        self.socket.sendall(data)



if __name__ == "__main__":
    server = ServerSocket()
    client = ClientSocket()

    server.Waiting()
    client.send()

