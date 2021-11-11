import pickle
import numpy as np
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split

def make_dataset(split_mode):
    assert split_mode in ['independent', 'dependent']

    with open('padded_data/data_length.pickle', 'rb') as f:
        data_length = pickle.load(f)

    with open('cleaved_data/data_length_dict.pickle', 'rb') as f:
        data_length_dict = pickle.load(f)

    if split_mode == 'independent':
        concated_x = np.empty((0, 6, 8))
        concated_y = np.empty((0))

        # Hard Coded because of not enough memory space.
        for data_number in data_length[:3]:
            for piece_number in data_length_dict[data_number]:
                temp_numpy = np.load("cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
                concated_x = np.concatenate((concated_x, temp_numpy), axis=0)

        for data_number in data_length[:3]:
            for piece_number in data_length_dict[data_number]:
                temp_numpy = np.load("cleaved_data/y_{}_{}.npy".format(data_number, piece_number))
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
                temp_numpy = np.load("cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
                concated_x = np.concatenate((concated_x, temp_numpy), axis=0)

        concated_y = np.empty((0))
        for data_number in data_length[3:]:
            for piece_number in data_length_dict[data_number]:
                temp_numpy = np.load("cleaved_data/y_{}_{}.npy".format(data_number, piece_number))
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

        np.save('train_test_data/indep_x_train.npy', x_train)
        np.save('train_test_data/indep_y_train.npy', y_train)
        
        np.save('train_test_data/indep_x_valid.npy', x_valid)
        np.save('train_test_data/indep_y_valid.npy', y_valid)

    else:
        train_x = np.empty((0, 6, 8))
        train_y = np.empty((0))

        # Hard Coded because of not enough memory space.
        # for data_number in data_length[:4]:
        #     train_x = np.empty((0, 6, 8))
        #     for piece_number in data_length_dict[data_number]:
        #         temp_numpy = []
        #         temp_numpy = np.load("cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
        #         print(data_number, piece_number)
        #         train_x = np.concatenate((train_x, temp_numpy), axis=0)
        #     np.save('train_test_data/dep_x_train_{}.npy'.format(data_number), train_x)

        for data_number in data_length[:4]:
            train_y = np.empty((0))
            for piece_number in data_length_dict[data_number]:
                temp_numpy = []
                temp_numpy = np.load("cleaved_data/y_{}_{}.npy".format(data_number, piece_number))
                train_y = np.concatenate((train_y, temp_numpy), axis=0)
            np.save('train_test_data/dep_y_train_{}.npy'.format(data_number), train_y)

        del train_x
        del train_y
        
        valid_x = np.empty((0, 6, 8))
        valid_y = np.empty((0))

        for data_number in data_length[4:]:
            for piece_number in data_length_dict[data_number]:
                temp_numpy = []
                temp_numpy = np.load("cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
                valid_x = np.concatenate((valid_x, temp_numpy), axis=0)
        np.save('train_test_data/dep_y_valid.npy', valid_x)
        del valid_x

        for data_number in data_length[4:]:
            for piece_number in data_length_dict[data_number]:
                temp_numpy = []
                temp_numpy = np.load("cleaved_data/y_{}_{}.npy".format(data_number, piece_number))
                valid_y = np.concatenate((valid_y, temp_numpy), axis=0)
        np.save('train_test_data/dep_y_train.npy', valid_y)
        del valid_y

if __name__ == '__main__':
    make_dataset(split_mode='dependent')