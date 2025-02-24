"""Implementation of the MNIST client and model."""

from typing import Tuple

import torch
from fl4health.clients.basic_client import BasicClient
from fl4health.clients.fed_prox_client import FedProxClient
from fl4health.utils.config import narrow_dict_type
from fl4health.utils.dataset import TensorDataset
from fl4health.utils.load_data import load_mnist_data
from fl4health.utils.sampler import DirichletLabelBasedSampler
from flwr.common.typing import Config
from torch import nn
from torch.nn.modules.loss import _Loss
from torch.optim import Optimizer
from torch.utils.data import DataLoader
from torchvision.datasets import MNIST

from florist.api.models.mnist import MnistNet


class MnistClient(BasicClient):  # type: ignore[misc]
    """Implementation of the MNIST client."""

    def get_data_loaders(self, config: Config) -> Tuple[DataLoader[TensorDataset], DataLoader[TensorDataset]]:
        """
        Return the data loader for MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (Tuple[DataLoader[MnistDataset], DataLoader[MnistDataset]]) a tuple with the train data loader
            and validation data loader respectively.
        """
        # Removing LeCun's website from the list of mirrors to pull MNIST dataset from
        # as it is timing out and adding considerable time to our tests
        mirror_url_to_remove = "http://yann.lecun.com/exdb/mnist/"
        if mirror_url_to_remove in MNIST.mirrors:
            MNIST.mirrors.remove(mirror_url_to_remove)

        train_loader, val_loader, _ = load_mnist_data(self.data_path, batch_size=int(config["batch_size"]))
        return train_loader, val_loader

    def get_model(self, config: Config) -> nn.Module:
        """
        Return the model for MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (torch.nn.Module) An instance of florist.api.clients.mnist.MnistNet.
        """
        return MnistNet()

    def get_optimizer(self, config: Config) -> Optimizer:
        """
        Return the optimizer for MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (torch.optim.Optimizer) An instance of torch.optim.SGD with learning
            rate of 0.001 and momentum of 0.9.
        """
        return torch.optim.SGD(self.model.parameters(), lr=0.001, momentum=0.9)

    def get_criterion(self, config: Config) -> _Loss:
        """
        Return the loss for MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (torch.nn.modules.loss._Loss) an instance of torch.nn.CrossEntropyLoss.
        """
        return torch.nn.CrossEntropyLoss()


class MnistFedProxClient(FedProxClient):  # type: ignore[misc]
    """Implementation of the FedProx client with the MNIST model."""

    def get_data_loaders(self, config: Config) -> Tuple[DataLoader[TensorDataset], DataLoader[TensorDataset]]:
        """
        Return the data loader for FedProx MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (Tuple[DataLoader[MnistDataset], DataLoader[MnistDataset]]) a tuple with the train data loader
            and validation data loader respectively.
        """
        # Removing LeCun's website from the list of mirrors to pull MNIST dataset from
        # as it is timing out and adding considerable time to our tests
        mirror_url_to_remove = "http://yann.lecun.com/exdb/mnist/"
        if mirror_url_to_remove in MNIST.mirrors:
            MNIST.mirrors.remove(mirror_url_to_remove)

        sampler = DirichletLabelBasedSampler(list(range(10)), sample_percentage=0.75, beta=1)
        batch_size = narrow_dict_type(config, "batch_size", int)
        train_loader, val_loader, _ = load_mnist_data(self.data_path, batch_size, sampler)
        return train_loader, val_loader

    def get_model(self, config: Config) -> nn.Module:
        """
        Return the model for FedProx MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (torch.nn.Module) An instance of florist.api.clients.mnist.MnistNet.
        """
        return MnistNet().to(self.device)

    def get_optimizer(self, config: Config) -> Optimizer:
        """
        Return the optimizer for FedProx MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (torch.optim.Optimizer) An instance of torch.optim.SGD with learning
            rate of 0.001 and momentum of 0.9.
        """
        return torch.optim.AdamW(self.model.parameters(), lr=0.01)

    def get_criterion(self, config: Config) -> _Loss:
        """
        Return the loss for FedProx MNIST data.

        :param config: (Config) the Config object for this client.
        :return: (torch.nn.modules.loss._Loss) an instance of torch.nn.CrossEntropyLoss.
        """
        return torch.nn.CrossEntropyLoss()
