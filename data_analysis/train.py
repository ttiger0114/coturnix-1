import torch
import torch.nn as nn
import datetime
import os
import numpy as np
from tqdm import tqdm

from autoencoder import AutoEncoder
from utils.stockdataset import StockDataset
from utils.get_logger import get_logger
from utils.earlystopper import EarlyStopper
from utils.get_dataloader import get_dataloader

def train_model(model, epochs, optimizer, start_time, device, early_stopper, logger):
    loss_fn = nn.MSELoss()

    train_losses = []
    valid_losses = []

    best_val_loss = np.Inf

    train_dataloader, valid_dataloader, test_dataloader = get_dataloader()

    for epoch in tqdm(range(epochs)):
        loss_sum = 0
        for x in train_dataloader:
            x = x.to(device)
            pred_x = model(x.view(x.shape[0], -1))
            loss = loss_fn(pred_x, x.view(x.shape[0], -1))
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            train_loss_sum += loss.item()

        train_losses.append(train_loss_sum/len(train_dataloader))
        msg = '{} Epoch, Train Mean Loss: {}'.format(epoch, train_loss_sum/len(train_dataloader))
        logger.info(msg)

        for x in valid_dataloader:
            with torch.no_grad():
                x = x.to(device)
                pred_x = model(x.view(x.shape[0], -1))
                loss = loss_fn(pred_x, x.view(x.shape[0], -1))

            valid_loss_sum += loss.item()

        val_losses.append(valid_loss_sum/len(d4rl_val_dataloader))
        msg = '{} Epoch, Validation Mean Loss: {}'.format(epoch, valid_loss_sum/len(valid_dataloader))
        logger.info(msg)

        train_losses.append(train_loss_sum / len(train_dataloader))
        valid_losses.append(valid_loss_sum / len(valid_dataloader))
        
        plt.plot(train_losses, label='train loss', color='r')
        plt.plot(val_losses, label='validation loss', color='b')

        if epoch == 0:
            plt.legend()

        plt.savefig(os.path.join('../result/', start_time, 'loss_graph', '.png'))
        np.save(os.path.join('../result/', start_time, 'train_losses.npy'), np.array(train_losses))
        np.save(os.path.join('../result/', start_time, 'val_losses.npy'), np.array(val_losses))

        early_stopper.check_early_stopping(valid_loss_sum / len(valid_dataloader))

        if early_stopper.save_model:
            torch.save(model.state_dict(), os.path.join('../result/', start_time, "model.pt"))
            msg = '\n\n\t Best Model Saved!!! \n'
            logger.info(msg)

        if early_stopper.stop:
            msg = '\n\n\t Early Stop by Patience Exploded!!! \n'
            logger.info(msg)
            break

    return model

if __name__ == '__main__':
    DATA_SIZE = 6
    DATA_DIMENSION = 8
    LATENT_DIMENSION = 4 
    DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

    model = AutoEncoder(DATA_SIZE * DATA_DIMENSION, LATENT_DIMENSION)
    model = model.to(DEVICE)

    start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%s")
    os.mkdir(os.path.join('result', start_time))

    system_logger = get_logger(name='autoencoder', file_path=os.path.join('result', start_time, 'train_log.log'))
    system_logger.info('===== Arguments information =====')

    system_logger.info('===== Model Structure =====')
    system_logger.info(model)

    mse_loss_function = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters())

    early_stopper = EarlyStopper(patience=20)
    train_model(model=model, optimizer=optimizer, epochs=100, start_time=start_time, device=DEVICE, early_stopper=early_stopper, logger=system_logger)