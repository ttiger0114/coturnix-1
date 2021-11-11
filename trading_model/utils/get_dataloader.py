import pickle
import numpy as np
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from utils.stockdataset import StockDataset
from sklearn.model_selection import train_test_split

def get_dataloader():
    
    x_train = np.load("../data_preprocess/train_test_data/dep_x_train.npy")
    y_train = np.load("../data_preprocess/train_test_data/dep_y_train.npy")

    x_valid = np.load("../data_preprocess/train_test_data/dep_x_valid.npy")
    y_valid = np.load("../data_preprocess/train_test_data/dep_y_valid.npy")

    train_dataset = StockDataset(x_train, y_train)
    valid_dataset = StockDataset(x_valid, y_valid)
    # test_dataset = StockDataset(x_test)

    train_dataloader = DataLoader(train_dataset, batch_size=10000, shuffle=True, num_workers=4)
    valid_dataloader = DataLoader(valid_dataset, batch_size=10000, shuffle=False, num_workers=4)
    # test_dataloader = DataLoader(test_dataset, batch_size=10000, shuffle=False)

    return train_dataloader, valid_dataloader
