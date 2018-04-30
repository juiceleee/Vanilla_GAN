import random
import matplotlib.pyplot as plt
import numpy as np
import datetime
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from tensorboardX import SummaryWriter

from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets("MNIST_data/")

learning_rate = 0.0002
training_epochs = 1000
batch_size = 100
noise_n = 100
flag = 0


# for Discriminator


class Discriminator(nn.Module):

    def __init__(self):
        super(Discriminator, self).__init__()
        self.pad = nn.ReplicationPad2d(1)
        self.h1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=(3, 3))
        self.h2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(3, 3))
        self.h3 = nn.Linear(in_features=28 * 28 * 64, out_features=625)
        self.h4 = nn.Linear(in_features=625, out_features=1)
        self.dropout = nn.Dropout(p=0.7)

    def forward(self, *input):
        x = input[0]
        x = torch.reshape(x, (-1, 1, 28, 28))
        x = self.pad(x)
        x = self.h1.forward(x)
        x = F.relu(x)
        x = self.pad(x)
        x = self.h2.forward(x)
        x = F.relu(x)
        x = torch.reshape(x, (-1, 28 * 28 * 64))
        x = self.h3.forward(x)
        x = F.relu(x)
        x = self.h4.forward(x)
        x = self.dropout.forward(x)
        x = F.sigmoid(x)

        return x


# for Generator
class Generator(nn.Module):

    def __init__(self):
        super(Generator, self).__init__()
        self.pad = nn.ReplicationPad2d(1)
        self.h1 = nn.Linear(noise_n, 256)
        self.h2 = nn.Linear(256, 512)
        self.h3 = nn.Linear(512, 784)

    def forward(self, *input):
        x = input[0]
        x = self.h1(x)
        x = F.relu(x)
        x = self.h2(x)
        x = F.relu(x)
        x = self.h3(x)
        x = F.sigmoid(x)
        return x


def make_noise(batch_size, noise_n):
    return np.random.normal(size=[batch_size, noise_n])


if __name__ == "__main__":
    G = Generator().cuda()
    D = Discriminator().cuda()
    opt_G = torch.optim.Adam(G.parameters(), lr=learning_rate)
    opt_D = torch.optim.Adam(D.parameters(), lr=learning_rate)
    total_batch = int(mnist.train.num_examples / batch_size)
    writer = SummaryWriter("log_dir")

    for epoch in range(training_epochs):
        for i in range(total_batch):
            X, _ = mnist.train.next_batch(batch_size)
            X = torch.Tensor(X).cuda()
            X.requires_grad_()

            noise = torch.Tensor(make_noise(batch_size, noise_n)).cuda()
            noise.requires_grad_()

            opt_D.zero_grad()
            opt_G.zero_grad()
            D_real = D(X)
            D_fake = D(G(noise))
            D_loss = -(torch.mean(torch.log(D_real) + torch.log(1 - D_fake)))
            G_loss = -torch.mean(torch.log(D_fake))
            D_loss.backward(retain_graph=True)
            G_loss.backward(retain_graph=True)
            opt_D.step()
            opt_G.step()
            if i % 10 == 0:
                writer.add_scalar("D_loss", D_loss, i+epoch*total_batch)
                writer.add_scalar("G_loss", G_loss, i+epoch*total_batch)
            if i % 100 == 0:
                print("EPOCH : {}, BATCH: {}\n".format(epoch, i), "D_loss : {}, G_loss : {}".format(D_loss, G_loss))
        writer.add_image("Epoch:{}".format(epoch), torch.reshape(G(noise[0]), (28, 28)))

    print('Learning finished')