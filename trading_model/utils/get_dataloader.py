import pickle
import numpy as np
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from utils.stockdataset import StockDataset
from sklearn.model_selection import train_test_split

def get_dataloader():
    with open('../data_preprocess/padded_data/data_length.pickle', 'rb') as f:
        data_length = pickle.load(f)

    with open('../data_preprocess/cleaved_data/data_length_dict.pickle', 'rb') as f:
        data_length_dict = pickle.load(f)

    concated_x = np.empty((0, 6, 8))

    # Hard Coded because of not enough memory space.
    for data_number in data_length[:3]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../data_preprocess/cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
            concated_x = np.concatenate((concated_x, temp_numpy), axis=0)

    concated_y = np.empty((0))
    for data_number in data_length[:3]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../data_preprocess/cleaved_data/y_{}_{}.npy".format(data_number, piece_number))
            concated_y = np.concatenate((concated_y, temp_numpy), axis=0)

    # seperate data into two pieces for small memory issue.
    x_train_1, x_valid_and_test_1 = train_test_split(concated_x.astype(np.float32), test_size=0.2, shuffle=True, random_state=42)
    x_valid_1, x_test_1 = train_test_split(x_valid_and_test_1, test_size=0.5, shuffle=True, random_state=42)

    y_train_1, y_valid_and_test_1 = train_test_split(concated_y.astype(np.float32), test_size=0.2, shuffle=True, random_state=42)
    y_valid_1, y_test_1 = train_test_split(y_valid_and_test_1, test_size=0.5, shuffle=True, random_state=42)

    del x_valid_and_test_1
    del y_valid_and_test_1
    del x_test_1
    del concated_x
    del concated_y

    concated_x = np.empty((0, 6, 8))

    for data_number in data_length[3:]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../data_preprocess/cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
            concated_x = np.concatenate((concated_x, temp_numpy), axis=0)

    concated_y = np.empty((0))
    for data_number in data_length[3:]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../data_preprocess/cleaved_data/y_{}_{}.npy".format(data_number, piece_number))
            concated_y = np.concatenate((concated_y, temp_numpy), axis=0)

    x_train_2, x_valid_and_test_2 = train_test_split(concated_x.astype(np.float32), test_size=0.2, shuffle=True, random_state=42)
    x_valid_2, x_test_2 = train_test_split(x_valid_and_test_2, test_size=0.5, shuffle=True, random_state=42)

    y_train_2, y_valid_and_test_2 = train_test_split(concated_y.astype(np.float32), test_size=0.2, shuffle=True, random_state=42)
    y_valid_2, y_test_2 = train_test_split(y_valid_and_test_2, test_size=0.5, shuffle=True, random_state=42)
    
    del x_valid_and_test_2
    del y_valid_and_test_2
    del x_test_2
    del concated_x
    del concated_y

    x_train = np.concatenate((x_train_1, x_train_2), axis=0)
    y_train = np.concatenate((y_train_1, y_train_2), axis=0)
    
    x_valid = np.concatenate((x_valid_1, x_valid_2), axis=0)
    y_valid = np.concatenate((y_valid_1, y_valid_2), axis=0)
    
    # x_test = np.concatenate((x_test_1, x_test_2), axis=0)
    # y_test = np.concatenate((y_test_1, y_test_2), axis=0)

    np.save('../data_preprocess/train_test_data/x_train.npy', x_train)
    np.save('../data_preprocess/train_test_data/y_train.npy', y_train)
    
    np.save('../data_preprocess/train_test_data/x_valid.npy', x_valid)
    np.save('../data_preprocess/train_test_data/y_valid.npy', y_valid)

    x_train, y_train, x_valid, y_valid = data_aggregation()

    train_dataset = StockDataset(x_train)
    valid_dataset = StockDataset(x_valid)
    # test_dataset = StockDataset(x_test)

    train_dataloader = DataLoader(train_dataset, batch_size=10000, shuffle=True, num_workers=4)
    valid_dataloader = DataLoader(valid_dataset, batch_size=10000, shuffle=False, num_workers=4)
    # test_dataloader = DataLoader(test_dataset, batch_size=10000, shuffle=False)

    return train_dataloader, valid_dataloader
