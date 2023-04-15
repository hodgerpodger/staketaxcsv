import base64
from functools import partial
import hashlib

from staketaxcsv.algo.api_algoindexer import AlgoIndexerAPI
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import (
    export_deposit_collateral_tx,
    export_swap_tx,
    export_unknown,
    export_withdraw_collateral_tx
)
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_algo_transfer,
    is_app_call,
    is_transaction_sender,
    is_transfer,
    is_transfer_receiver_non_zero_asset
)
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

# For reference:
# https://docs.deflex.fi/
# https://github.com/deflex-fi/deflex-abis

APPLICATION_ID_DEFLEX_ORDER_ROUTER = [
    989365103,
    956739264,
    951874839,
    892463450,
    1032513697,  # Folks Finance
]
APPLICATION_ID_DEFLEX_REGISTRY = 949209670

DEFLEX_LIMIT_ORDER_APPROVAL_HASH = "fabca7ecf7e45acc21df99d8b98d48d729153272a72d15e2f6b923af3e8458da"

DEFLEX_TRANSACTION_OPT_IN = "TMSORQ=="         # "User_opt_into_assets" ABI selector
DEFLEX_TRANSACTION_SWAP = "P2FHIA=="           # "User_swap" ABI selector
DEFLEX_TRANSACTION_SWAP_FINALIZE = "tTD7Hw=="  # "User_swap_finalize" ABI selector

DEFLEX_TRANSACTION_CREATE_ORDER = "Ai+ORg=="   # "User_create_order" ABI selector
DEFLEX_TRANSACTION_CANCEL_ORDER = "dXwdeg=="   # "User_cancel_order" ABI selector
DEFLEX_TRANSACTION_FILL_ORDER_INIT = "Ynj8hA=="      # "Backend_fill_order_initialize" ABI selector
DEFLEX_TRANSACTION_FILL_ORDER_FINALIZE = "QZXMuQ=="  # "Backend_fill_order_finalize" ABI selector
DEFLEX_TRANSACTION_CLOSE_ESCROW = "jVTQ1A=="   # "Backend_close_escrow" ABI selector


class Deflex(Dapp):
    def __init__(self, indexer: AlgoIndexerAPI, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.limit_order_apps = self._get_deflex_limit_order_apps(account)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "Deflex"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return (self._is_deflex_routed_swap(group)
                or self._is_deflex_limit_order_fill(group)
                or self._is_deflex_limit_order_create(group)
                or self._is_deflex_limit_order_cancel(group))

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        if self._is_deflex_routed_swap(group):
            self._handle_deflex_routed_swap(group, txinfo)

        elif self._is_deflex_limit_order_fill(group):
            self._handle_deflex_limit_order_fill(group, txinfo)

        elif self._is_deflex_limit_order_create(group):
            self._handle_deflex_limit_order_create(group, txinfo)

        elif self._is_deflex_limit_order_cancel(group):
            self._handle_deflex_limit_order_cancel(group, txinfo)

        else:
            export_unknown(self.exporter, txinfo)

    def _get_deflex_limit_order_apps(self, account):
        apps = []
        if account is None:
            return apps

        created_apps = account.get("created-apps", [])
        for app in created_apps:
            approval_program = app.get("params", {}).get("approval-program", "")
            if approval_program:
                approval_hash = hashlib.sha256(base64.b64decode(approval_program)).hexdigest()
                if DEFLEX_LIMIT_ORDER_APPROVAL_HASH == approval_hash:
                    apps.append(app["id"])

        return apps

    def _is_deflex_routed_swap(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        transaction = group[0]
        if not is_transfer(transaction):
            return False

        if not is_transaction_sender(self.user_address, transaction):
            return False

        i = 1
        transaction = group[i]
        if is_algo_transfer(transaction) and is_transaction_sender(self.user_address, transaction):
            i += 1

        if i == length:
            return False

        return is_app_call(group[i], app_args=DEFLEX_TRANSACTION_SWAP_FINALIZE)

    def _is_deflex_limit_order_fill(self, group):
        if len(group) != 2:
            return False

        if not is_app_call(group[0], self.limit_order_apps, DEFLEX_TRANSACTION_FILL_ORDER_FINALIZE):
            return False

        return is_app_call(group[1], APPLICATION_ID_DEFLEX_REGISTRY, DEFLEX_TRANSACTION_CLOSE_ESCROW)

    def _is_deflex_limit_order_create(self, group):
        if len(group) < 4:
            return False

        if not is_app_call(group[-1], self.limit_order_apps, DEFLEX_TRANSACTION_CREATE_ORDER):
            return False

        transaction = group[-2]
        if not is_transfer(transaction):
            return False

        if not is_transaction_sender(self.user_address, transaction):
            return False

        transaction = group[-3]
        if not is_algo_transfer(transaction):
            return False

        return is_transaction_sender(self.user_address, transaction)

    def _is_deflex_limit_order_cancel(self, group):
        if len(group) != 2:
            return False

        if not is_app_call(group[0], self.limit_order_apps, DEFLEX_TRANSACTION_CANCEL_ORDER):
            return False

        return is_app_call(group[1], APPLICATION_ID_DEFLEX_REGISTRY, DEFLEX_TRANSACTION_CLOSE_ESCROW)

    def _handle_deflex_routed_swap(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[0])

        i = 1
        transaction = group[i]
        if is_algo_transfer(transaction) and is_transaction_sender(self.user_address, transaction):
            fee_asset = get_transfer_asset(transaction)
            fee_amount += fee_asset.uint_amount
            i += 1

        receive_asset = get_inner_transfer_asset(group[i],
                                                filter=partial(is_transfer_receiver_non_zero_asset, self.user_address))

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name)

    def _handle_deflex_limit_order_fill(self, group, txinfo):
        receive_transaction = group[0]
        app_id = receive_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
        round = receive_transaction["confirmed-round"]
        full_group = self.indexer.get_transactions_by_app(app_id, round)

        if not full_group:
            return export_unknown(self.exporter, txinfo)

        send_transaction = next((tx for tx in full_group
            if is_app_call(tx, app_id, DEFLEX_TRANSACTION_FILL_ORDER_INIT)), None)
        if send_transaction is None:
            return export_unknown(self.exporter, txinfo)

        send_asset = get_inner_transfer_asset(send_transaction)

        receive_asset = get_inner_transfer_asset(receive_transaction,
                                                filter=partial(is_transfer_receiver_non_zero_asset, self.user_address))

        comment = self.name + " Order Fill"
        export_withdraw_collateral_tx(self.exporter, txinfo, send_asset, 0, comment, 0)
        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, 0, comment, 1)

    def _handle_deflex_limit_order_create(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_transaction = group[-2]
        send_asset = get_transfer_asset(send_transaction)

        fee_transaction = group[-3]
        fee_asset = get_transfer_asset(fee_transaction)
        fee_amount += fee_asset.uint_amount

        comment = self.name + " Create Order"
        export_deposit_collateral_tx(self.exporter, txinfo, send_asset, fee_amount, comment, 1)

    def _handle_deflex_limit_order_cancel(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[0],
                                                filter=partial(is_transfer_receiver_non_zero_asset, self.user_address))
        export_withdraw_collateral_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name + " Order Cancel")
