import torch
import torch.nn as nn
import datetime
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from models._1D_CNN1 import _1D_CNN1
from utils.get_logger import get_logger
from utils.earlystopper import EarlyStopper
from utils.get_dataloader import get_dataloader

def train_model(model, epochs, optimizer, start_time, device, early_stopper, logger, tick=False, tick_precision=100):
    loss_fn = nn.CrossEntropyLoss()

    train_losses = []
    train_accuracies = []
    tick_train_losses = []
    tick_train_accuracies = []
    
    valid_losses = []
    valid_accuracies = []
    tick_valid_losses = []
    tick_valid_accuracies = []

    best_val_loss = np.Inf
    train_dataloader, valid_dataloader = get_dataloader()

    if tick:
        train_tick_frequency = len(train_dataloader) // tick_precision

    for epoch in tqdm(range(epochs)):
        train_loss_sum = 0
        train_sum_acc = 0
        train_total_cnt = 0

        valid_loss_sum = 0
        valid_sum_acc = 0
        valid_total_cnt = 0

        tick_train_loss_sum = 0
        tick_train_sum_acc = 0
        tick_train_total_cnt = 0

        tick_valid_loss_sum = 0
        tick_valid_sum_acc = 0
        tick_valid_total_cnt = 0

        for i, (x, y) in tqdm(enumerate(train_dataloader), total=len(train_dataloader)):
            out = model(x.to(device))
            y = y.long().to(device)
            loss = loss_fn(out, y)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            
            train_loss_sum += loss.item()
            predict = torch.argmax(out, dim=1)
            train_sum_acc += torch.sum(predict == y)
            train_total_cnt += len(y)

            if tick:
                tick_train_loss_sum += loss.item()
                tick_train_sum_acc += torch.sum(predict == y)
                tick_train_total_cnt += len(y)

                if i % train_tick_frequency == 0 and i:
                    tick_train_loss_mean = tick_train_loss_sum / train_tick_frequency
                    tick_train_accuracy = tick_train_sum_acc / tick_train_total_cnt
                    msg = '\t{} tick, Tick Train Mean Loss: {}, Tick Train Accuracy: {}'.format(i / train_tick_frequency, tick_train_loss_mean, tick_train_accuracy)
                    logger.info(msg)

                    tick_train_losses.append(tick_train_loss_mean)
                    tick_train_accuracies.append(tick_train_accuracy)

                    tick_train_loss_sum = 0
                    tick_train_sum_acc = 0
                    tick_train_total_cnt = 0

                    with torch.no_grad():
                        for x, y in valid_dataloader:
                            out = model(x.to(device))
                            y = y.long().to(device)
                            loss = loss_fn(out, y)

                            tick_valid_loss_sum += loss.item()
                            predict = torch.argmax(out, dim=1)
                            tick_valid_sum_acc += torch.sum(predict == y)
                            tick_valid_total_cnt += len(y)

                        tick_valid_loss_mean = tick_valid_loss_sum / len(valid_dataloader)
                        tick_valid_accuracy = tick_valid_sum_acc / tick_valid_total_cnt

                        tick_valid_losses.append(tick_valid_loss_mean)
                        tick_valid_accuracies.append(tick_valid_accuracy)
                            
                        tick_valid_loss_sum = 0
                        tick_valid_sum_acc = 0
                        tick_valid_total_cnt = 0
                    

        train_accuracy = train_sum_acc/train_total_cnt
        train_loss_mean = train_loss_sum/len(train_dataloader)
        msg = '{} Epoch, Train Mean Loss: {}, Train Accuracy: {}'.format(epoch, train_loss_mean, train_accuracy)
        logger.info(msg)

        with torch.no_grad():
            for x, y in valid_dataloader:
                out = model(x.to(device))
                y = y.long().to(device)
                loss = loss_fn(out, y)

                valid_loss_sum += loss.item()
                predict = torch.argmax(out, dim=1)
                valid_sum_acc += torch.sum(predict == y)
                valid_total_cnt += len(y)
        
        valid_accuracy = valid_sum_acc/valid_total_cnt
        valid_loss_mean = valid_loss_sum/len(valid_dataloader)
        msg = '{} Epoch, Train Mean Loss: {}, Train Accuracy: {}'.format(epoch, valid_loss_mean, valid_accuracy)
        logger.info(msg)

        train_losses.append(train_loss_mean)
        valid_losses.append(valid_loss_mean)

        train_accuracies.append(train_accuracy)
        valid_accuracies.append(valid_accuracy)
        
        # Loss graph
        plt.plot(train_losses, label='train loss', color='r')
        plt.plot(valid_losses, label='validation loss', color='b')

        if epoch == 0:
            plt.legend()

        plt.savefig(os.path.join('./result/', start_time, 'loss_graph.png'))
        np.save(os.path.join('./result/', start_time, 'train_losses.npy'), np.array(train_losses))
        np.save(os.path.join('./result/', start_time, 'valid_losses.npy'), np.array(valid_losses))
        
        plt.clf()

        # Accuracy graph
        plt.plot(train_accuracies, label='train accuracy', color='r')
        plt.plot(valid_accuracies, label='validation accuracy', color='b')

        if epoch == 0:
            plt.legend()

        plt.savefig(os.path.join('./result/', start_time, 'accuracy_graph.png'))
        np.save(os.path.join('./result/', start_time, 'train_accuracies.npy'), np.array(train_accuracies))
        np.save(os.path.join('./result/', start_time, 'valid_accuracies.npy'), np.array(valid_accuracies))

        early_stopper.check_early_stopping(valid_loss_mean)

        if early_stopper.save_model:
            torch.save(model.state_dict(), os.path.join('./result/', start_time, "model.pt"))
            msg = '\n\n\t Best Model Saved!!! \n'
            logger.info(msg)

        if early_stopper.stop:
            msg = '\n\n\t Early Stop by Patience Exploded!!! \n'
            logger.info(msg)
            break

    return model

if __name__ == '__main__':
    # DATA_SIZE = 6
    # DATA_DIMENSION = 8
    # LATENT_DIMENSION = 4
    # model = AutoEncoder(DATA_SIZE * DATA_DIMENSION, LATENT_DIMENSION)
    DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

    model = _1D_CNN1(n=1, p=0)
    model = model.to(DEVICE)

    start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not os.path.exists(os.path.join("result")):
        os.mkdir(os.path.join('result'))

    os.mkdir(os.path.join('result', start_time))

    system_logger = get_logger(name="1D_CNN1", file_path=os.path.join('result', start_time, 'train_log.log'))
    system_logger.info('===== Arguments information =====')

    system_logger.info('===== Model Structure =====')
    system_logger.info('\n\n')
    system_logger.info(model)

    optimizer = torch.optim.Adam(model.parameters())

    early_stopper = EarlyStopper(patience=20)
    train_model(model=model, optimizer=optimizer, epochs=3, start_time=start_time, device=DEVICE, early_stopper=early_stopper, logger=system_logger, tick=True, tick_precision=100)