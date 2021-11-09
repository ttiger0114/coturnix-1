import time
import torch
import torch.nn as nn
import numpy as np
import tqdm
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from kiwoom_stock import LoopBackSocket as lb

# from model import model as md
# from model.model import Simple1DCNN

device = 'cuda' if torch.cuda.is_available() else 'cpu'

if __name__ == "__main__":
    #PATH = 'modelList/시초돌파_p15_l075_45.pt'
    '''
    PATH = 'modelList/시초돌파_5ch.pt'
    DATA_PATH = 'data/val_data_시초돌파.npy'
    BPS_PATH = 'data/val_break_points_시초돌파.npy'

    DATA = np.load(DATA_PATH)
    BPS = np.load(BPS_PATH)

    model = torch.load(PATH,map_location=device)

    MainWindow = md.MainWindow(model)
    MainWindow.MakeDataSet(DATA,BPS)
    MainWindow.MakeDataLoader(32)
    MainWindow.Predict(10)

    '''
    server = lb.ServerSocket()
    server.AcceptWait()
    while True:

        data = server.Waiting()
        if str(type(data)) == "<class 'numpy.ndarray'>":
            print(torch.tensor(data))
        
        server.SendData(['code', "buy" ])
    
            
