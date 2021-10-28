import pickle
from stockdataset import StockDataset

def data_aggregation():
    with open('padded_data/data_length.pickle', 'rb') as f:
        data_length = pickle.load(f)

    with open('cleaved_data/data_length_dict.pickle', 'rb') as f:
        data_length_dict = pickle.load(f)

    concated_x = np.empty((0, 6, 8))

    # Hard Coded because of not enough memory space.
    for data_number in data_length[:3]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../../data_preprocess/cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
            concated_x = np.concatenate((concated_x, temp_numpy), axis=0)

    concated_y = np.empty((0))
    for data_number in data_length[:3]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../../data_preprocess/cleaved_data/x_{}_{}.npy/y_{}_{}.npy".format(data_number, piece_number))
            concated_y = np.concatenate((concated_y, temp_numpy), axis=0)

    # seperate data into two pieces for small memory issue.
    x_train_1, x_valid_and_test_1 = train_test_split(concated_x.astype(np.float32), test_size=0.2, shuffle=True, random_state=42)
    x_valid_1, x_test_1 = train_test_split(x_valid_and_test_1, test_size=0.5, shuffle=True, random_state=42)

    del concated_x
    del concated_y

    for data_number in data_length[3:]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../../data_preprocess/cleaved_data/x_{}_{}.npy".format(data_number, piece_number))
            concated_x = np.concatenate((concated_x, temp_numpy), axis=0)

    concated_y = np.empty((0))
    for data_number in data_length[3:]:
        for piece_number in data_length_dict[data_number]:
            temp_numpy = np.load("../../data_preprocess/cleaved_data/x_{}_{}.npy/y_{}_{}.npy".format(data_number, piece_number))
            concated_y = np.concatenate((concated_y, temp_numpy), axis=0)

    x_train_2, x_valid_and_test_2 = train_test_split(concated_x.astype(np.float32), test_size=0.2, shuffle=True, random_state=42)
    x_valid_2, x_test_2 = train_test_split(x_valid_and_test_2, test_size=0.5, shuffle=True, random_state=42)
    
    del concated_x
    del concated_y

    x_train = np.concatenate((x_train_1, x_train_2), axis=0)
    y_train = np.concatenate((y_train_1, y_train_2), axis=0)
    
    x_valid = np.concatenate((x_valid_1, x_valid_2), axis=0)
    y_valid = np.concatenate((y_valid_1, y_valid_2), axis=0)
    
    x_test = np.concatenate((x_test_1, x_test_2), axis=0)
    y_test = np.concatenate((y_test_1, y_test_2), axis=0)

    return x_train, y_train, x_valid, y_valid, x_test, y_test

def get_dataloader():
    x_train, y_train, x_valid, y_valid, x_test, y_test = data_aggregation()

    train_dataset = StockDataset(x_train)
    valid_dataset = StockDataset(x_valid)
    testd_dataset = StockDataset(x_test)

    train_dataloader = DataLoader(train_dataset, batch_size=10000, shuffle=True)
    valid_dataloader = DataLoader(valid_dataset, batch_size=10000, shuffle=False)
    test_dataloader = DataLoader(test_dataset, batch_size=10000, shuffle=False)

    return train_dataloader, valid_dataloader, test_dataloader
