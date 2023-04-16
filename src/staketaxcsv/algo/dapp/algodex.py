import base64
import json
import re

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import export_swap_tx
from staketaxcsv.algo.transaction import get_transaction_note, get_transfer_asset
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

# For reference check the whitepaper appendix:
# https://github.com/algodex/algodex-public-documents/blob/master/Algodex%20Whitepaper%201.0.pdf

APPLICATION_ID_ALGODEX_BUY = 354073718
APPLICATION_ID_ALGODEX_SELL = 354073834

ALGODEX_LIMIT_ORDER_OPEN = "open"
ALGODEX_LIMIT_ORDER_CLOSE = "close"
ALGODEX_LIMIT_ORDER_PARTIAL = "execute_partial"
ALGODEX_LIMIT_ORDER_FULL = "execute_full"

ALGODEX_LIMIT_ORDER_ACTIONS = [
    ALGODEX_LIMIT_ORDER_OPEN,
    ALGODEX_LIMIT_ORDER_CLOSE,
    ALGODEX_LIMIT_ORDER_PARTIAL,
    ALGODEX_LIMIT_ORDER_FULL
]

ALGODEX_TRANSACTION_ORDER_EXECUTE = "ZXhlY3V0ZQ=="  # "execute"

ORDER_TYPE_BUY = "buy"
ORDER_TYPE_SELL = "sell"


class AlgoDex(Dapp):
    def __init__(self, indexer: Indexer, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter
        # <initiator_address>-<asset_id>-[<action>]_[algo|asa]
        self.order_pattern = re.compile(r"^\w+-\d+-\[(?P<action>\w+)\]_\[(?:algo|asa)\]")

    @property
    def name(self):
        return "AlgoDex"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        length = len(group)
        if length < 1 or length > 5:
            return False

        transaction = group[0]
        txtype = transaction["tx-type"]
        if txtype == co.TRANSACTION_TYPE_APP_CALL:
            app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
            if app_id != APPLICATION_ID_ALGODEX_BUY and app_id != APPLICATION_ID_ALGODEX_SELL:
                return False

        note = get_transaction_note(transaction)
        if not note:
            if txtype == co.TRANSACTION_TYPE_APP_CALL:
                appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
                return ALGODEX_TRANSACTION_ORDER_EXECUTE in appl_args
            return False

        if len(note) < len(self.user_address):
            return False

        try:
            order = json.loads(note)
        except Exception:
            return False
        key = next(iter(order))

        match = self.order_pattern.match(key)
        if not match:
            return False

        action_type = match.group("action")

        return action_type in ALGODEX_LIMIT_ORDER_ACTIONS

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        transaction = group[0]
        txtype = transaction["tx-type"]
        note = get_transaction_note(transaction)
        if not note:
            if txtype == co.TRANSACTION_TYPE_APP_CALL:
                appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
                if ALGODEX_TRANSACTION_ORDER_EXECUTE in appl_args:
                    if group[-1]["sender"] == self.user_address:
                        self._handle_algodex_market_order_buy_side(group, txinfo)
                    else:
                        self._handle_algodex_market_order_sell_side(group, txinfo)
            return

        order = json.loads(note)
        key = next(iter(order))
        order_details = order.get(key)
        initiator_address = key.split("-", 1)[0]
        order_type = order_details["escrowOrderType"]
        if ALGODEX_LIMIT_ORDER_PARTIAL in key:
            if order_type == ORDER_TYPE_BUY:
                if initiator_address == self.user_address:
                    self._handle_algodex_partial_buy_sell_side(group, txinfo)
                else:
                    self._handle_algodex_partial_buy_buy_side(group, txinfo)
            else:
                if initiator_address == self.user_address:
                    self._handle_algodex_partial_sell_buy_side(group, txinfo)
                else:
                    self._handle_algodex_partial_sell_sell_side(group, txinfo)
        elif ALGODEX_LIMIT_ORDER_FULL in key:
            if order_type == ORDER_TYPE_BUY:
                if initiator_address == self.user_address:
                    self._handle_algodex_full_buy_sell_side(group, txinfo)
                else:
                    self._handle_algodex_full_buy_buy_side(group, txinfo)
            else:
                if initiator_address == self.user_address:
                    self._handle_algodex_full_sell_buy_side(group, txinfo)
                else:
                    self._handle_algodex_full_sell_sell_side(group, txinfo)
        # Ignore open and close orders

    # AlgoDex whitepaper: Diagram 7
    def _handle_algodex_partial_buy_sell_side(self, group, txinfo):
        fee_amount = 0
        receive_transaction = group[1]
        receive_asset = get_transfer_asset(receive_transaction)

        send_transaction = group[2]
        fee_amount = send_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)

        fee_transaction = group[3]
        fee_amount += fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Partial Limit Sell Order")

    def _handle_algodex_partial_buy_buy_side(self, group, txinfo):
        fee_amount = 0
        receive_transaction = group[1]
        receive_asset = get_transfer_asset(receive_transaction)

        app_transaction = group[0]
        n, d, _ = self._get_order_details(app_transaction)

        send_asset = Algo((receive_asset.uint_amount * d) / n)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Partial Limit Buy Order")

    # AlgoDex whitepaper: Diagram 11
    def _handle_algodex_partial_sell_buy_side(self, group, txinfo):
        fee_amount = 0
        send_transaction = group[1]
        fee_amount = send_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)

        receive_transaction = group[2]
        receive_asset = get_transfer_asset(receive_transaction)
        if receive_asset.zero() and len(group) > 4:
            # ASA opt-in
            receive_transaction = group[3]
            receive_asset = get_transfer_asset(receive_transaction)
            fee_transaction = group[4]
        else:
            fee_transaction = group[3]

        fee_amount += fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Partial Limit Buy Order")

    def _handle_algodex_partial_sell_sell_side(self, group, txinfo):
        fee_amount = 0
        receive_transaction = group[1]
        receive_asset = get_transfer_asset(receive_transaction)

        app_transaction = group[0]
        n, d, asset_id = self._get_order_details(app_transaction)

        send_asset = Asset(asset_id, (receive_asset.uint_amount * n) / d)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Partial Limit Sell Order")

    # AlgoDex whitepaper: Diagram 6
    def _handle_algodex_full_buy_sell_side(self, group, txinfo):
        fee_amount = 0
        receive_transaction = group[1]
        receive_asset = get_transfer_asset(receive_transaction)

        send_transaction = group[2]
        fee_amount = send_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Full Limit Sell Order")

    def _handle_algodex_full_buy_buy_side(self, group, txinfo):
        fee_amount = 0
        receive_transaction = group[2]
        receive_asset = get_transfer_asset(receive_transaction)

        app_transaction = group[0]
        n, d, _ = self._get_order_details(app_transaction)

        send_asset = Algo((receive_asset.uint_amount * d) / n)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Full Limit Buy Order")

    # AlgoDex whitepaper: Diagram 10
    def _handle_algodex_full_sell_buy_side(self, group, txinfo):
        fee_amount = 0
        send_transaction = group[1]
        fee_amount = send_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)

        receive_transaction = group[2]
        receive_asset = get_transfer_asset(receive_transaction)
        if receive_asset.zero() and len(group) > 3:
            # ASA opt-in
            receive_transaction = group[3]
            receive_asset = get_transfer_asset(receive_transaction)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Full Limit Buy Order")

    def _handle_algodex_full_sell_sell_side(self, group, txinfo):
        fee_amount = 0
        receive_transaction = group[1]
        receive_asset = get_transfer_asset(receive_transaction)

        app_transaction = group[0]
        n, d, asset_id = self._get_order_details(app_transaction)

        send_asset = Asset(asset_id, (receive_asset.uint_amount * n) / d)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Full Limit Sell Order")

    # Undocumented
    def _handle_algodex_market_order_buy_side(self, group, txinfo):
        send_transaction = group[1]
        fee_amount = send_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)

        receive_transaction = group[2]
        receive_asset = get_transfer_asset(receive_transaction)
        if receive_asset.zero() and len(group) > 4:
            # ASA opt-in
            receive_transaction = group[3]
            receive_asset = get_transfer_asset(receive_transaction)
            fee_transaction = group[4]
        else:
            fee_transaction = group[3]

        fee_amount += fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Market Buy Order")

    def _handle_algodex_market_order_sell_side(self, group, txinfo):
        fee_amount = 0
        app_transaction = group[0]
        n, d, asset_id = self._get_order_details(app_transaction)

        receive_transaction = group[1]
        receive_asset = get_transfer_asset(receive_transaction)
        send_asset = Asset(asset_id, (receive_asset.uint_amount * n) / d)

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name + " Market Sell Order")

    def _get_order_details(self, transaction):
        appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        # <n>-<d>-<min>-<asset_id>
        order_details = base64.b64decode(appl_args[1]).decode("utf-8").split("-")
        n = int(order_details[0])
        d = int(order_details[1])
        asset_id = int(order_details[3])
        return n, d, asset_id
