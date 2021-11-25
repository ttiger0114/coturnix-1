import time
import datetime
import torch
import torch.nn as nn
import numpy as np
import tqdm
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from kiwoom_stock import LoopBackSocket as lb
from tqdm.auto import tqdm
import math
import copy
from torch.nn import TransformerEncoder, TransformerEncoderLayer

# from model import model as md
# from model.model import Simple1DCNN



class TransformerModel(nn.Module):
    def __init__(self, ninp=125, nhead=5, nhid=125, nlayers=6, dropout=0.5):
        super(TransformerModel, self).__init__()
        self.model_type = 'Transformer'
        #self.pos_encoder = PositionalEncoding(ninp)
        encoder_layers = TransformerEncoderLayer(ninp, nhead, nhid, dropout)
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)
        self.ninp = ninp
        self.embedding = nn.Linear(5,70)
        self.classification = nn.Linear(420,3)


    def generate_square_subsequent_mask(self):
        mask = (torch.triu(torch.ones(6, 6)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask

    def forward(self, src, src_mask):
        a,b=src.size(0),src.size(1)
        src = src.view(a*b,-1)
        src = self.embedding(src)
        src = src.view(a,b,-1)
        src = src.transpose(0,1)
        #src = self.pos_encoder(src)
        output = self.transformer_encoder(src, src_mask)
        output = output.transpose(0,1)
        output = output.reshape(output.size(0),-1)
        output = self.classification(output)
        return output

class PositionalEncoding(nn.Module):

    def __init__(self, d_model, dropout=0.1, max_len=6):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / 12))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class SimpleDataset(torch.utils.data.Dataset):
    def __init__(self, data, labels):
        super().__init__()
        #self.data = np.concatenate((data[:,:,:5],data[:,:,6:]),axis=2)
        self.data = data[:,:,:5]
        self.labels = labels
        self.labels[self.labels==3]=0
        # for i in range(len(self.data)):
        #   self.data[i, :,:4] = (self.data[i, :,:4]-1)*100
        #   self.data[i, :,4] = self.data[i, :,4]*0.1
        
    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

    def __len__(self):
        return len(self.data)


if __name__ == "__main__":
    path = "ctnx_models/transformer_3_1112_pricecond_zeropadding_trade18_075_5features.pt"
    model = TransformerModel(ninp=70,nhid=70,nlayers=6,nhead=7,dropout=0.0)
    
    # self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    device = torch.device('cpu')
    # model = TransformerModel(ninp=70,nhid=70,nlayers=6,nhead=7,dropout=0.0).to('cuda')
    model = torch.load(path, map_location = device)
    print("Model Load Complete")

    server = lb.ServerSocket()
    server.AcceptWait()

    while True:
        received_data = server.Waiting()
        code = received_data[0]
        stock_data = received_data[1]
        ret = []
        
        now = datetime.datetime.now()
        if now.hour <= 9 and now.minute <= 50 :
        # if now.hour >= 9:
            if str(type(stock_data)) == "<class 'numpy.ndarray'>":
                stock_labels = np.ones((stock_data.shape[0]))
                test_dataset = SimpleDataset(stock_data,stock_labels)
                test_dataloader = DataLoader(test_dataset, batch_size=1024, shuffle=False, drop_last=False)
                # print(torch.tensor(data))
                model.eval()
                # outs = []
                with torch.no_grad():
                    for i, (data, gt) in enumerate(test_dataloader):
                        now = datetime.datetime.now()
                        print("input")
                        data = data.float()
                        # print(data)
                        print(data.shape)
                        src_mask=model.generate_square_subsequent_mask()
                        out=model(data,src_mask)
                        gt = torch.tensor(gt, dtype=torch.long)

                        confidence = torch.softmax(out, dim = 1)
                        confidence = confidence.clone().detach().numpy()

                        c = torch.argmax(out,dim=1)
                        outs = c.clone().detach().numpy()
                        
                        condi = np.where(outs == 2)[0]
                        if len(condi) != 0:
                            for code_idx in condi:
                                ret.append(code[code_idx])
                            print(ret)
                            print()
                            server.SendData(["buy", ret])
                        
                        server.SendData(["confidence", code, confidence])
                        
        else:
            print("Time Out")

        
    