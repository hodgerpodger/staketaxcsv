from abc import ABC, abstractmethod
import os
import traceback
from importlib import util

from staketaxcsv.algo.api.indexer import Indexer
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
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        """ Dapp constructor

        Args:
            indexer (Indexer): Algorand indexer REST API.
            user_address (str): User account address.
            account (dict): Account object as returned by the indexer,
                see schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Account
            exporter (Exporter): Exporter object used to add rows to the CSV.
        """
        super().__init__()

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def get_extra_transactions(self) -> list:
        """ Get extra transactions that are related to the dapp and the user
        but do not originate from their own address. These transactions will
        later on be fed to :meth:`dapp.Dapp.is_dapp_transaction` and
        :meth:`dapp.Dapp.handle_dapp_transaction` if applicable.

        Returns:
            list: List of transaction objects as returned by the indexer,\
                see schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Transaction
        """
        pass

    @abstractmethod
    def is_dapp_transaction(self, group: list) -> bool:
        """ Get whether the transaction group belongs to this dapp. If this returns `true`
        the same group will be fed to :meth:`dapp.Dapp.handle_dapp_transaction`.

        Args:
            group (list): List of transaction objects that share the same group id. Note\
                this may not be the full transaction group, as the indexer will only return\
                transactions where the provided address is referenced in either `sender`,\
                `receiver` or `application accounts`.

        Returns:
            bool: `true` when the transaction group belongs to this dapp.
        """
        pass

    @abstractmethod
    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        """ Handle the transaction group and, if applicable, add the corresponding
        rows to the CSV Exporter.

        Args:
            group (list): List of transaction objects that share the same group id. Note\
                this may not be the full transaction group, as the indexer will only return\
                transactions where the provided address is referenced in either `sender`,\
                `receiver` or `application accounts`.
            txinfo (TxInfo): Transaction info object to be passed to `Exporter` when adding CSV rows.
        """
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
