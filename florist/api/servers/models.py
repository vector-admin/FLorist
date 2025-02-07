"""Common functions and definitions for servers."""

from enum import Enum
from functools import partial
from typing import Any, Callable, TypeAlias

from fl4health.client_managers.base_sampling_manager import SimpleClientManager
from fl4health.reporting.base_reporter import BaseReporter
from fl4health.server.adaptive_constraint_servers.fedprox_server import FedProxServer
from fl4health.server.base_server import FlServer
from fl4health.strategies.fedavg_with_adaptive_constraint import FedAvgWithAdaptiveConstraint
from fl4health.utils.metric_aggregation import evaluate_metrics_aggregation_fn, fit_metrics_aggregation_fn
from flwr.common.parameter import ndarrays_to_parameters
from flwr.server.strategy import FedAvg
from torch import nn
from typing_extensions import Self

from florist.api.models.mnist import MnistNet
from florist.api.servers.config_parsers import ConfigParser


GetServerFunction: TypeAlias = Callable[[nn.Module, int, list[BaseReporter], dict[str, Any]], FlServer]

class ServerFactory:
    def __init__(self, get_server_function: GetServerFunction):
        self.get_server_function = get_server_function

    def get_server_constructor(
        self,
        model: nn.Module,
        n_clients: int,
        reporters: list[BaseReporter],
        server_config: dict[str, Any],
    ) -> Callable[[Any], FlServer]:
        return partial(self.get_server_function, model, n_clients, reporters, server_config)


class Model(Enum):
    """Enumeration of supported models."""

    MNIST_FEDAVG = "MNIST with FedAvg"
    MNIST_FEDPROX = "MNIST with FedProx"

    @classmethod
    def class_for_model(cls, model: Self) -> type[nn.Module]:
        """
        Return the class for a given model.

        :param model: (Model) The model enumeration object.
        :return: (type[torch.nn.Module]) A torch.nn.Module class corresponding to the given model.
        :raises ValueError: if the client is not supported.
        """
        if model in [Model.MNIST_FEDAVG, Model.MNIST_FEDPROX]:
            return MnistNet

        raise ValueError(f"Model {model.value} not supported.")

    @classmethod
    def config_parser_for_model(cls, model: Self) -> ConfigParser:
        """
        Return the config parser for a given model.

        :param model: (Model) The model enumeration object.
        :return: (type[torch.nn.Module]) A torch.nn.Module class corresponding to the given model.
        :raises ValueError: if the client is not supported.
        """
        if model == Model.MNIST_FEDAVG:
            return ConfigParser.BASIC
        if model == Model.MNIST_FEDPROX:
            return ConfigParser.FEDPROX

        raise ValueError(f"Model {model.value} not supported.")

    @classmethod
    def server_factory_for_model(cls, model: Self) -> ServerFactory:
        """
        Return the server factory class for a given model.

        :param model: (Model) The model enumeration object.
        :return: (type[AbstractServerFactory]) A AbstractServerFactory class corresponding to the given model.
        :raises ValueError: if the client is not supported.
        """
        if model == Model.MNIST_FEDAVG:
            return ServerFactory(get_server_function=get_fedavg_server)
        if model == Model.MNIST_FEDPROX:
            return ServerFactory(get_server_function=get_fedprox_server)

        raise ValueError(f"Model {model.value} not supported.")

    @classmethod
    def list(cls) -> list[str]:
        """
        List all the supported models.

        :return: (list[str]) a list of supported models.
        """
        return [model.value for model in Model]


def fit_config_function(server_config: dict[str, Any], current_server_round: int) -> dict[str, int]:
    return {
        **server_config,
        "current_server_round": current_server_round,
    }

def get_fedavg_server(
    model: nn.Module,
    n_clients: int,
    reporters: list[BaseReporter],
    server_config: dict[str, Any],
) -> FlServer:
    fit_config_fn = partial(fit_config_function, server_config)  # type: ignore
    initial_model_parameters = ndarrays_to_parameters([val.cpu().numpy() for _, val in model.state_dict().items()])
    strategy = FedAvg(
        min_fit_clients=n_clients,
        min_evaluate_clients=n_clients,
        min_available_clients=n_clients,
        on_fit_config_fn=fit_config_fn,
        on_evaluate_config_fn=fit_config_fn,
        fit_metrics_aggregation_fn=fit_metrics_aggregation_fn,
        evaluate_metrics_aggregation_fn=evaluate_metrics_aggregation_fn,
        initial_parameters=initial_model_parameters,
    )
    client_manager = SimpleClientManager()
    return FlServer(strategy=strategy, client_manager=client_manager, reporters=reporters)


def get_fedprox_server(
    model: nn.Module,
    n_clients: int,
    reporters: list[BaseReporter],
    server_config: dict[str, Any],
) -> FlServer:
    fit_config_fn = partial(fit_config_function, server_config)  # type: ignore
    initial_model_parameters = ndarrays_to_parameters([val.cpu().numpy() for _, val in model.state_dict().items()])
    strategy = FedAvgWithAdaptiveConstraint(
        min_fit_clients=n_clients,
        min_evaluate_clients=n_clients,
        # Server waits for min_available_clients before starting FL rounds
        min_available_clients=n_clients,
        on_fit_config_fn=fit_config_fn,
        # We use the same fit config function, as nothing changes for eval
        on_evaluate_config_fn=fit_config_fn,
        fit_metrics_aggregation_fn=fit_metrics_aggregation_fn,
        evaluate_metrics_aggregation_fn=evaluate_metrics_aggregation_fn,
        initial_parameters=initial_model_parameters,
        adapt_loss_weight=server_config["adapt_proximal_weight"],
        initial_loss_weight=server_config["initial_proximal_weight"],
        loss_weight_delta=server_config["proximal_weight_delta"],
        loss_weight_patience=server_config["proximal_weight_patience"],
    )
    client_manager = SimpleClientManager()
    return FedProxServer(client_manager=client_manager, strategy=strategy, model=None, reporters=reporters)
