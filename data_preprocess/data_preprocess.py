# make data labels and cleave data
import pickle
from tqdm import tqdm
import numpy as np

DATA_LENGTH = 6
LABEL_DISTANCE = 6
DECISION_THRESHOLD = 0.0037
LABEL_RATIO_CORRECTION = 0
SAMPLING_FREQUENCY = 2

with open('padded_data/data_length.pickle', 'rb') as f:
    data_length = pickle.load(f)

data_length_dict = dict()
for length in data_length:
    data_length_dict[length] = []

for data_index in data_length:
    with open('./padded_data/data_{}.pickle'.format(data_index), 'rb') as f:
        data = list()
        data = pickle.load(f)

    preprocessed_x = list()
    preprocessed_y = list()
 
    for j, day in tqdm(enumerate(data), total=len(data)):
        day = np.array(day)
        
        # divide prices by first open price
        # make cumulative data temporal
        rolled = np.roll(day[:, -2:], 1, axis=0)
        rolled[0, :] = 0
        day[:, -2:] = day[:, -2:] - rolled
        day[:, :4] = day[:, :4] / day[0, 0]

        for i in range(len(day) - (DATA_LENGTH + LABEL_DISTANCE)):
            if i % SAMPLING_FREQUENCY == 1:
                continue

            reference_closing_price = day[DATA_LENGTH + i - 1, 3]
            high_price_forward = day[DATA_LENGTH + i:DATA_LENGTH + i + LABEL_DISTANCE, 1]
            low_price_forward = day[DATA_LENGTH + i:DATA_LENGTH + i + LABEL_DISTANCE, 2]

            high_threshold = np.sum(high_price_forward > reference_closing_price * (1 + DECISION_THRESHOLD))
            low_threshold = np.sum(low_price_forward < reference_closing_price * (1 - DECISION_THRESHOLD - LABEL_RATIO_CORRECTION))

            if (not high_threshold and not low_threshold):
                label = 1 # osciliate
            elif (not high_threshold and low_threshold):
                label = 0 # sell on loss
            elif (high_threshold and not low_threshold):
                label = 2 # sell on profit
            else:
                high_trigger = np.argmax(high_price_forward > reference_closing_price * (1 + DECISION_THRESHOLD))
                low_trigger = np.argmax(low_price_forward < reference_closing_price * (1 - DECISION_THRESHOLD - LABEL_RATIO_CORRECTION))

                if high_trigger == low_trigger:
                    label = 3
                elif high_trigger > low_trigger:                   
                    label = 0
                else:
                    label = 2

            x = day[i:i+DATA_LENGTH]

            preprocessed_x.append(x.tolist())
            preprocessed_y.append(label)

        # Considering Colab Pro Memory Space, 8000 is chosen as appropriate on-memory numpy length.
        if (j % (8000 * SAMPLING_FREQUENCY) == 0 and j) or j == len(data) - 1:
            data_length_dict[data_index].append(j)

            preprocessed_x = np.array(preprocessed_x)
            preprocessed_y = np.array(preprocessed_y)

            np.save('cleaved_data/x_{}_{}.npy'.format(data_index, j), preprocessed_x)
            np.save('cleaved_data/y_{}_{}.npy'.format(data_index, j), preprocessed_y)

            preprocessed_x = list()
            preprocessed_y = list()

with open('cleaved_data/data_length_dict.pickle'.format(i), 'wb') as f:
    pickle.dump(data_length_dict, f)