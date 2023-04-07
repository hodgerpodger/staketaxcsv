from abc import ABC, abstractmethod
import os
import traceback
from importlib import util

from staketaxcsv.algo.api_algoindexer import AlgoIndexerAPI
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo


class Dapp(ABC):
    plugins = []

    # For every class that inherits from the current,
    # the class name will be added to plugins
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

    @abstractmethod
    def __init__(self, indexer: AlgoIndexerAPI, wallet_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__()

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def get_extra_transactions(self) -> list:
        pass

    @abstractmethod
    def is_dapp_transaction(self, group: list) -> bool:
        pass

    @abstractmethod
    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        pass


def load_module(path):
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


path = os.path.abspath(__file__)
dirpath = os.path.dirname(path)

for fname in os.listdir(dirpath):
    if not fname.startswith('.') and not fname.startswith('__') and fname.endswith('.py'):
        try:
            load_module(os.path.join(dirpath, fname))
        except Exception:
            traceback.print_exc()
