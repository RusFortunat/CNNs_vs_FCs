# I followed this PyTorch tutorial to write the code: https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html
# Change 'torchvision.datasets.CIFAR10' to whatever dataset you want to work with.
# The list of datasets available for the training can be found here: https://pytorch.org/vision/0.8/datasets.html#mnist
# Take care of whether the images you load are gray-scale or colored, that changes the number of input channels

import time
import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


class FCNet(nn.Module):
    def __init__(self, image_shape, hidden_layer_FC1, hidden_layer_FC2):
        super().__init__()
        self.fc1 = nn.Linear(image_shape, hidden_layer_FC1) # DIFFERENT FOR DIFFERENT DATA SETS; I'm lazy & stupid to automize it on the go
        self.fc2 = nn.Linear(hidden_layer_FC1, hidden_layer_FC2)
        self.fc3 = nn.Linear(hidden_layer_FC2, 10)

    def forward(self, x):
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# LeNet architecture
class ConvNet(nn.Module):
    def __init__(self, in_channels, hidden_layer_FC1, hidden_layer_FC2):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 6, 5) # in_channels=3, out_channels=6, kernel_size=5, stride=1, padding=0
        self.pool = nn.MaxPool2d(2, 2) # kernel_size=2, stride=2; reduces H & W of the input by 2
        self.conv2 = nn.Conv2d(6, 16, 5) 
        self.fc1 = nn.Linear(256, hidden_layer_FC1) # the input size here has to be computed correctly to avoid the matrix multiplication error
        self.fc2 = nn.Linear(hidden_layer_FC1, hidden_layer_FC2)
        self.fc3 = nn.Linear(hidden_layer_FC2, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# Have to wrap the main to run the code on Windows, sorry not sorry
def main():

    batch_size = 4

    # for grayscale images
    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize([0.5], [0.5])])

    # for colored images
    #transform = transforms.Compose(
    #    [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    
    # download images from CIFAR10 datasel
    trainset = torchvision.datasets.KMNIST(root='./data', train=True, download=True, transform=transform)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size, shuffle=True, num_workers=2)

    testset = torchvision.datasets.KMNIST(root='./data', train=False, download=True, transform=transform)
    testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    # just to get image dimensions for FC network
    dataiter = iter(trainloader)
    images, labels = next(dataiter)
    image_dims = images[0].shape[0] * images[0].shape[1] * images[0].shape[2] # here I am assuming that the image has [NChannels x H x W] .shape format

    print(f'Image dimensions: {images[0].shape[0]} x {images[0].shape[1]} x {images[0].shape[2]}')
    print(f'Flattened vector size: {image_dims}')

    # initialize instances of FC and ConvNet classes
    in_channels = 1 # important for CNN networks: 1 for grayscale, 3 for colored
    hidden_layer_FC1 = 200 # 120 tutorial value
    hidden_layer_FC2 = 100 # 84 tutorial value
    fcNet = FCNet(image_dims, hidden_layer_FC1, hidden_layer_FC2)
    convNet = ConvNet(in_channels, hidden_layer_FC1, hidden_layer_FC2)
    num_of_FC_params = count_parameters(fcNet)
    num_of_CNN_params = count_parameters(convNet)

    criterion = nn.CrossEntropyLoss()
    
    # train FC model
    start_time = time.time()
    optimizerFC = optim.SGD(fcNet.parameters(), lr=0.001, momentum=0.9)
    for epoch in range(2):  # loop over the dataset multiple times
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            # get the inputs; data is a list of [inputs, labels]
            inputs, labels = data

            # zero the parameter gradients
            optimizerFC.zero_grad()

            # forward + backward + optimize
            outputs = fcNet(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizerFC.step()

            # print statistics
            running_loss += loss.item()
            if i % 2000 == 1999:    # print every 2000 mini-batches
                print(f'[{epoch + 1}, {i + 1:5d}] FC loss: {running_loss / 2000:.3f}')
                running_loss = 0.0

    FC_training_time = time.time() - start_time
    print('Finished Training FC model')

    # train CNN model
    start_time = time.time()
    optimizerCNN = optim.SGD(convNet.parameters(), lr=0.001, momentum=0.9)
    for epoch in range(2):  # loop over the dataset multiple times
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            # get the inputs; data is a list of [inputs, labels]
            inputs, labels = data

            # zero the parameter gradients
            optimizerCNN.zero_grad()

            # forward + backward + optimize
            outputs = convNet(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizerCNN.step()

            # print statistics
            running_loss += loss.item()
            if i % 2000 == 1999:    # print every 2000 mini-batches
                print(f'[{epoch + 1}, {i + 1:5d}] CNN loss: {running_loss / 2000:.3f}')
                running_loss = 0.0

    CNN_training_time = time.time() - start_time
    print('Finished Training CNN model')

    # run the trained model through the whole dataset
    correctFC = 0
    correctCNN = 0
    total = 0
    # since we're not training, we don't need to calculate the gradients for our outputs
    with torch.no_grad():
        for data in testloader:
            images, labels = data
            # calculate outputs by running images through the network
            outputFC = fcNet(images)
            outputsCNN = convNet(images)
            # the class with the highest energy is what we choose as prediction
            _, predictedFC = torch.max(outputFC.data, 1)
            _, predictedCNN = torch.max(outputsCNN.data, 1)
            total += labels.size(0)
            correctFC += (predictedFC == labels).sum().item()
            correctCNN += (predictedCNN == labels).sum().item()
    

    print(f'FC training time: {FC_training_time} sec')
    print(f'CNN training time: {CNN_training_time} sec')
    print(f'Number of FC model parameters: {num_of_FC_params}')
    print(f'Number of CNN model parameters: {num_of_CNN_params}')
    print(f'Accuracy of the FC network on the 10000 test images: {100 * correctFC // total} %')
    print(f'Accuracy of the CNN network on the 10000 test images: {100 * correctCNN // total} %')


if __name__ == '__main__':
    main()
