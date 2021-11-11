import torch
import torch.nn as nn

BN_MOMENTUM=0.1
class 1D_CNN1(nn.Module):
    def __init__(self,n,p):
        super().__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(7, 32*n, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32*n, momentum=BN_MOMENTUM),
            nn.ReLU(inplace=True),
            nn.Dropout(p),
        )
        self.conv2 = nn.Sequential(
            nn.Conv1d(32*n, 32*n, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(32*n, momentum=BN_MOMENTUM),
            nn.ReLU(inplace=True),
            nn.Dropout(p),
        )
        self.conv3 = nn.Sequential(
            nn.Conv1d(32*n, 64*n, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(64*n, momentum=BN_MOMENTUM),
            nn.ReLU(inplace=True),
            nn.Dropout(p),
        )
        self.conv4 = nn.Sequential(
            nn.Conv1d(64*n, 64*n, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(64*n, momentum=BN_MOMENTUM),
            nn.ReLU(inplace=True),
            nn.Dropout(p),
        )
        self.conv5 = nn.Sequential(
            nn.Conv1d(64*n, 128*n, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(128*n, momentum=BN_MOMENTUM),
            nn.ReLU(inplace=True),
            nn.Dropout(p),
        )
        self.conv6 = nn.Sequential(
            nn.Conv1d(128*n, 128*n, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(128*n, momentum=BN_MOMENTUM),
            nn.ReLU(inplace=True),
            nn.Dropout(p),
        )
        self.linear1 = nn.Sequential(
            nn.Linear(128*n*6,128*n*6),
            nn.ReLU(),
            nn.Linear(6*128*n,3),
        )
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def forward(self, x):
        x=x.to(self.device)
        x= torch.transpose(x,1,2)
        x= self.conv1(x)
        x= self.conv2(x)
        x= self.conv3(x)
        x= self.conv4(x)
        x= self.conv5(x)
        x= self.conv6(x)
        x=x.view(x.size(0),-1)
        x= self.linear1(x)
        return x