from functools import partial

from staketaxcsv.algo.api_algoindexer import AlgoIndexerAPI
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import export_participation_rewards, export_swap_tx, export_unknown
from staketaxcsv.algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_lp_add_group,
    is_lp_remove_group,
    is_swap_group
)
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_app_call,
    is_asset_optin,
    is_transaction_sender,
    is_transfer,
    is_transfer_receiver
)
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

APPLICATION_ID_PACT_ROUTER = 887109719

# TODO update names when app ABI is published
PACT_TRANSACTION_ROUTED_SWAP_1 = "hN2OEA=="    # ABI selector
PACT_TRANSACTION_ROUTED_SWAP_2 = "OowGzw=="    # ABI selector

PACT_TRANSACTION_SWAP = "U1dBUA=="           # "SWAP"
PACT_TRANSACTION_LP_ADD = "QURETElR"         # "ADDLIQ"
PACT_TRANSACTION_LP_REMOVE = "UkVNTElR"      # "REMLIQ"


class Pact(Dapp):
    def __init__(self, indexer: AlgoIndexerAPI, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "Pact"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return (self._is_pact_routed_swap(group)
                    or self._is_pact_swap(group)
                    or self._is_pact_lp_add(group)
                    or self._is_pact_lp_remove(group))

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        reward = Algo(group[0]["sender-rewards"])
        export_participation_rewards(reward, self.exporter, txinfo)

        txinfo.comment = self.name
        if self._is_pact_routed_swap(group):
            self._handle_pact_routed_swap(group, txinfo)

        elif self._is_pact_swap(group):
            handle_swap(self.user_address, group, self.exporter, txinfo)

        elif self._is_pact_lp_add(group):
            handle_lp_add(group, self.exporter, txinfo)

        elif self._is_pact_lp_remove(group):
            handle_lp_remove(group, self.exporter, txinfo)

        else:
            export_unknown(self.exporter, txinfo)

    def _is_pact_swap(self, group):
        if not is_swap_group(self.user_address, group):
            return False

        return is_app_call(group[-1], app_args=PACT_TRANSACTION_SWAP)

    def _is_pact_routed_swap(self, group):
        if len(group) < 2:
            return False

        i = 0
        if is_asset_optin(group[i]):
            i += 1

        transaction = group[i]
        if not is_transfer(transaction):
            return False

        if not is_transaction_sender(self.user_address, transaction):
            return False

        if is_asset_optin(transaction):
            return False

        return is_app_call(group[-1],
                           APPLICATION_ID_PACT_ROUTER,
                           [PACT_TRANSACTION_ROUTED_SWAP_1, PACT_TRANSACTION_ROUTED_SWAP_2])

    def _is_pact_lp_add(self, group):
        if not is_lp_add_group(self.user_address, group):
            return False

        return is_app_call(group[-1], app_args=PACT_TRANSACTION_LP_ADD)

    def _is_pact_lp_remove(self, group):
        if not is_lp_remove_group(self.user_address, group):
            return False

        return is_app_call(group[-1], app_args=PACT_TRANSACTION_LP_REMOVE)

    def _handle_pact_routed_swap(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        length = len(group)
        i = 0
        while i < length and is_asset_optin(group[i]):
            i += 1

        send_asset = None
        receive_asset = None
        for transaction in group[i:]:
            if is_transfer(transaction):
                asset = get_transfer_asset(transaction)
                send_asset = asset if send_asset is None else send_asset + asset
            elif is_app_call(transaction, app_args=[PACT_TRANSACTION_SWAP,
                                                    PACT_TRANSACTION_ROUTED_SWAP_1,
                                                    PACT_TRANSACTION_ROUTED_SWAP_2]):
                asset = get_inner_transfer_asset(transaction,
                                                 filter=partial(is_transfer_receiver, self.user_address))
                if asset is not None:
                    receive_asset = asset if receive_asset is None else receive_asset + asset

        if send_asset is not None and receive_asset is not None:
            export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Router")
        else:
            export_unknown(self.exporter, txinfo)
