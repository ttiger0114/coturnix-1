import glob
import os
import pandas as pd

data_path= 'D:/data'
data_path_list=glob.glob(data_path+'/*')
cnt=0

for file in data_path_list:
    temp=pd.read_csv(file, encoding='euc-kr')
    temp=temp.loc[temp['시간'] <930]
    temp_group = temp.groupby('날짜')
    print(temp_group.groups)
    cnt+=1
    break

print(cnt)