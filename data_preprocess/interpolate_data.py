import numpy as np
import pandas as pd
from tqdm import tqdm
import os
import pickle

# ['날짜', '시간', '시가', '고가', '저가', '종가', '거래량', '거래대금', '누적체결매도수량', '누적체결매수수량']
remastered_data = list()
file_information = list()
file_path = 'data/{}'.format('/data/kosdaq')
file_name_list = os.listdir(file_path)
file_length = list()

for i, file_name in tqdm(enumerate(file_name_list), total=len(file_name_list)):
    # Considering Colab Pro Memory Space, 300 is chosen as appropriate list length.
    if (i % 300 == 0 and i != 0) or (i == len(file_name_list) - 1):
        with open('padded_data/data_{}.pickle'.format(i), 'wb') as f:
            pickle.dump(remastered_data, f)
    
        with open('padded_data/metadata_{}.pickle'.format(i), 'wb') as f:
            pickle.dump(file_information, f)
        remastered_data.clear()
        file_information.clear()

        file_length.append(i)

    full_path = os.path.join(file_path, file_name)
    raw_df = pd.read_csv(full_path, encoding='euc-kr')

    if raw_df.empty:
        continue

    time_in_str = raw_df.iloc[:, 1].astype(str).values

    data_per_day = list()
    data_row = list()

    next_expected_date = '20200730' # initial date
    next_expected_time = 9 * 60 + 1
    recent_row = [0, 0, 0, 0, 0, 0, 0, 0] # initialize recent 
    # '시가', '고가', '저가', '종가', '거래량', '거래대금', '누적체결매도수량', '누적체결매수수량'

    # In data of day, interpolate zero padding
    remastered_data.append(data_per_day)
    for j in range(raw_df.shape[0]):
        # append a list 'data per day', which is connected by pointer.
        data_row = raw_df.values[j].tolist()
        date = raw_df.iloc[j, 0]
        hour = int(time_in_str[j][:-2])
        minute = int(time_in_str[j][-2:])
        time_in_minutes = 60 * hour + minute
        data_row = data_row[2:]

        # If 'Date' Changes and data_per_day list has any data
        if next_expected_date != date and data_per_day:
            data_per_day = data_per_day.copy() # Leave existing list pointer
            data_per_day = list()
            remastered_data.append(data_per_day)
            next_expected_date = date
            next_expected_time = time_in_minutes
            file_information.append([file_name, next_expected_date, next_expected_time])
        
        # Data row Jump happened, interpolate it with zero padding.
        if next_expected_time != time_in_minutes:
            recent_row[0] = recent_row[3]
            recent_row[1] = recent_row[3]
            recent_row[2] = recent_row[3]
            recent_row[3] = recent_row[3]
            recent_row[4] = 0 # 거래량
            recent_row[5] = 0 # 거래대금
            while next_expected_time != time_in_minutes:
                # recent_row[1] = next_expected_time # 시간
                data_per_day.append(recent_row.copy())
                file_information.append([file_name, next_expected_date, next_expected_time])
                next_expected_time += 1
        
        file_information.append([file_name, date, time_in_minutes])
        
        data_per_day.append(data_row)
        recent_row = data_row.copy()

        next_expected_time += 1
        next_expected_date = date

with open('padded_data/data_length.pickle'.format(i), 'wb') as f:
    pickle.dump(file_length, f)