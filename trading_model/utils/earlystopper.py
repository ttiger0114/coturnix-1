import numpy as np

class EarlyStopper():
    def __init__(self, patience=20):
        self.patience = patience
        self.anger = 0
        self.best_loss = np.Inf
        self.stop = False
        self.save_model = False

    def check_early_stopping(self, validation_loss):
        if self.best_loss == np.Inf:
            self.best_loss = validation_loss

        elif self.best_loss < validation_loss:
            self.anger += 1
            self.save_model = False

            if self.anger >= self.patience:
                self.stop = True

        elif self.best_loss >= validation_loss:
            self.save_model = True
            self.anger = 0
            self.best_loss = validation_loss