import torch
import torch.nn as nn

class StockDataset(torch.utils.data.Dataset):
    def __init__(self, data, labels):
        super().__init__()
        #self.data = np.concatenate((data[:,:,:5],data[:,:,6:]),axis=2)
        self.data = data[:,:,:5]
        self.labels = labels
        self.labels[self.labels==3]=0
        
    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

    def __len__(self):
        return len(self.data)