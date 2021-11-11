import numpy as np
import pandas as pd
import copy
from tqdm import tqdm
import os
import pickle
from collections import deque

FILE_PATH = 'data/kosdaq'
FILTER_N_TRANSACTION = 47000
TRADE_VOLUME_MEAN_LEN = 5

# ['날짜', '시간', '시가', '고가', '저가', '종가', '거래량', '거래대금', '누적체결매도수량', '누적체결매수수량']
file_path = FILE_PATH
file_name_list = os.listdir(file_path)
file_length = list()

file_size = []

for file_name in sorted(file_name_list):
    full_path = os.path.join(file_path, file_name)
    raw_df = pd.read_csv(full_path, encoding='euc-kr')
    file_size.append(raw_df.shape[0])

filtered_stock_item = np.array(sorted(file_name_list))[np.array(file_size) > FILTER_N_TRANSACTION]
padded_data = list()

for i, file_name in tqdm(enumerate(filtered_stock_item), total=len(filtered_stock_item)):
    # Considering Colab Pro Memory Space, 300 is chosen as appropriate list length.
    if (i % 300 == 0 and i != 0) or (i == len(filtered_stock_item) - 1):
        with open('padded_data/data_{}.pickle'.format(i)', 'wb') as f:
            pickle.dump(padded_data, f)
        padded_data.clear()
        file_length.append(i)

    full_path = os.path.join(file_path, file_name)
    raw_df = pd.read_csv(full_path, encoding='euc-kr')

    if raw_df.empty:
        continue

    time_in_str = raw_df.iloc[:, 1].astype(str).values
    
    data_per_day = list()
    data_row = list()

    first_transaction = True
    trade_volume = 0
    trade_volume_history = deque(maxlen = TRADE_VOLUME_MEAN_LEN)

    # In data of day, interpolate zero padding
    for j in range(raw_df.shape[0]):
        # append a list 'data per day', which is connected by pointer.
        data_row = raw_df.values[j].tolist()
        date = raw_df.iloc[j, 0]
        hour = int(time_in_str[j][:-2])
        minute = int(time_in_str[j][-2:])
        time_in_minutes = 60 * hour + minute
        data_row = data_row[2:]

        if first_transaction:
            next_expected_date = date # initial date
            next_expected_time = time_in_minutes
            first_transaction = False

        # If 'Date' Changes and data_per_day list has any data
        if next_expected_date != date:
            if len(trade_volume_history) == TRADE_VOLUME_MEAN_LEN:                                                                                 
                mean_trade_vol = sum(trade_volume_history) / TRADE_VOLUME_MEAN_LEN
                trade_volume_history.append(trade_volume / 380)
                trade_volume = 0

                data_per_day = np.array(data_per_day).astype(np.float32)
                if mean_trade_vol == 0:
                    print("Trade volumes are zero in {} streaks. {} at {} , {}".format(TRADE_VOLUME_MEAN_LEN, date, time_in_minutes, file_name))

                data_per_day[:, 4] = (data_per_day[:, 4] / mean_trade_vol)
                data_per_day[:, 6] = (data_per_day[:, 6] / mean_trade_vol)
                data_per_day[:, 7] = (data_per_day[:, 7] / mean_trade_vol)

                data_per_day = data_per_day.tolist()
                padded_data.append(copy.deepcopy(data_per_day))

                data_per_day = list()
                next_expected_time = time_in_minutes
                next_expected_date = date

            else:
                data_per_day = list()
                trade_volume_history.append(trade_volume / 380)
                trade_volume = 0
                
                next_expected_time = time_in_minutes
                next_expected_date = date

        # Data row Jump happened, interpolate it with zero padding.
        if next_expected_time != time_in_minutes:
            recent_row[0] = recent_row[3]
            recent_row[1] = recent_row[3]
            recent_row[2] = recent_row[3]
            recent_row[4] = 0 # 거래량
            recent_row[5] = 0 # 거래대금

            while next_expected_time != time_in_minutes:
                data_per_day.append(copy.deepcopy(recent_row))
                next_expected_time += 1
        
        data_per_day.append(data_row)
        recent_row = copy.deepcopy(data_row)
        trade_volume += data_row[4]

        next_expected_time += 1
        next_expected_date = date

with open('padded_data/data_length.pickle', 'wb') as f:
    pickle.dump(data_length, f)