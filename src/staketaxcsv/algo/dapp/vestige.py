from functools import partial

from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import export_swap_tx, export_unknown
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_app_call,
    is_transfer,
    is_transfer_receiver
)
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo


APPLICATION_ID_VESTIGE_SWAP_V1 = 818176933
APPLICATION_ID_VESTIGE_SWAP_V3 = 1026089225

VESTIGE_V1_TRANSACTION_CALL = "Y2FsbA=="  # "call"
# TODO update names when app ABI is published
VESTIGE_V3_TRANSACTION_SWAP_INIT = "NhyEdw=="
VESTIGE_V3_TRANSACTION_SWAP_SWAP = "sogXLw=="
VESTIGE_V3_TRANSACTION_SWAP_FINALIZE = "Exz+tw=="


class Vestige(Dapp):
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "Vestige"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return self._is_vestige_swap_v1(group) or self._is_vestige_swap_v3(group)

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        if self._is_vestige_swap_v1(group):
            self._handle_vestige_swap_v1(group, txinfo)

        elif self._is_vestige_swap_v3(group):
            self._handle_vestige_swap_v3(group, txinfo)

        else:
            export_unknown(self.exporter, txinfo)

    def _is_vestige_swap_v1(self, group):
        if len(group) != 2:
            return False

        if not is_transfer(group[0]):
            return False

        return is_app_call(group[1], APPLICATION_ID_VESTIGE_SWAP_V1, VESTIGE_V1_TRANSACTION_CALL)

    def _is_vestige_swap_v3(self, group):
        if len(group) < 4:
            return False

        if not is_app_call(group[0], APPLICATION_ID_VESTIGE_SWAP_V3, VESTIGE_V3_TRANSACTION_SWAP_INIT):
            return False

        if not is_transfer(group[1]):
            return False

        if not is_app_call(group[2], APPLICATION_ID_VESTIGE_SWAP_V3, VESTIGE_V3_TRANSACTION_SWAP_SWAP):
            return False

        return is_app_call(group[-1], APPLICATION_ID_VESTIGE_SWAP_V3, VESTIGE_V3_TRANSACTION_SWAP_FINALIZE)

    def _handle_vestige_swap_v1(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[0])
        receive_asset = get_inner_transfer_asset(group[1],
                                                filter=partial(is_transfer_receiver, self.user_address))

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name)

    def _handle_vestige_swap_v3(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[1])
        receive_asset = get_inner_transfer_asset(group[-1],
                                                filter=partial(is_transfer_receiver, self.user_address))

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name)
