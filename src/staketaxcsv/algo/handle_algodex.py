import base64
import json
import re

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.export_tx import export_swap_tx
from staketaxcsv.algo.transaction import get_transaction_note, get_transfer_asset

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

# <initiator_address>-<asset_id>-[<action>]_[algo|asa]
order_pattern = re.compile(r"^\w+-\d+-\[(?P<action>\w+)\]_\[(?:algo|asa)\]")


def is_algodex_transaction(wallet_address, group):
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
    if note is None:
        if txtype == co.TRANSACTION_TYPE_APP_CALL:
            appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
            return ALGODEX_TRANSACTION_ORDER_EXECUTE in appl_args
        return False

    if len(note) < len(wallet_address):
        return False

    try:
        order = json.loads(note)
    except Exception:
        return False
    key = next(iter(order))

    match = order_pattern.match(key)
    if not match:
        return False

    action_type = match.group("action")

    return action_type in ALGODEX_LIMIT_ORDER_ACTIONS


def handle_algodex_transaction(wallet_address, group, exporter, txinfo):
    transaction = group[0]
    txtype = transaction["tx-type"]
    note = get_transaction_note(transaction)
    if note is None:
        if txtype == co.TRANSACTION_TYPE_APP_CALL:
            appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
            if ALGODEX_TRANSACTION_ORDER_EXECUTE in appl_args:
                if group[-1]["sender"] == wallet_address:
                    _handle_algodex_market_order_buy_side(group, exporter, txinfo)
                else:
                    _handle_algodex_market_order_sell_side(group, exporter, txinfo)
        return

    order = json.loads(note)
    key = next(iter(order))
    order_details = order.get(key)
    initiator_address = key.split("-", 1)[0]
    order_type = order_details["escrowOrderType"]
    if ALGODEX_LIMIT_ORDER_PARTIAL in key:
        if order_type == ORDER_TYPE_BUY:
            if initiator_address == wallet_address:
                _handle_algodex_partial_buy_sell_side(group, exporter, txinfo)
            else:
                _handle_algodex_partial_buy_buy_side(group, exporter, txinfo)
        else:
            if initiator_address == wallet_address:
                _handle_algodex_partial_sell_buy_side(group, exporter, txinfo)
            else:
                _handle_algodex_partial_sell_sell_side(group, exporter, txinfo)
    elif ALGODEX_LIMIT_ORDER_FULL in key:
        if order_type == ORDER_TYPE_BUY:
            if initiator_address == wallet_address:
                _handle_algodex_full_buy_sell_side(group, exporter, txinfo)
            else:
                _handle_algodex_full_buy_buy_side(group, exporter, txinfo)
        else:
            if initiator_address == wallet_address:
                _handle_algodex_full_sell_buy_side(group, exporter, txinfo)
            else:
                _handle_algodex_full_sell_sell_side(group, exporter, txinfo)
    # Ignore open and close orders


# AlgoDex whitepaper: Diagram 7
def _handle_algodex_partial_buy_sell_side(group, exporter, txinfo):
    fee_amount = 0
    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    send_transaction = group[2]
    fee_amount = send_transaction["fee"]
    send_asset = get_transfer_asset(send_transaction)

    fee_transaction = group[3]
    fee_amount += fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Partial Limit Sell Order")


def _handle_algodex_partial_buy_buy_side(group, exporter, txinfo):
    fee_amount = 0
    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    app_transaction = group[0]
    n, d, _ = _get_order_details(app_transaction)

    send_asset = Algo((receive_asset.uint_amount * d) / n)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Partial Limit Buy Order")


# AlgoDex whitepaper: Diagram 11
def _handle_algodex_partial_sell_buy_side(group, exporter, txinfo):
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

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Partial Limit Buy Order")


def _handle_algodex_partial_sell_sell_side(group, exporter, txinfo):
    fee_amount = 0
    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    app_transaction = group[0]
    n, d, asset_id = _get_order_details(app_transaction)

    send_asset = Asset(asset_id, (receive_asset.uint_amount * n) / d)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Partial Limit Sell Order")


# AlgoDex whitepaper: Diagram 6
def _handle_algodex_full_buy_sell_side(group, exporter, txinfo):
    fee_amount = 0
    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    send_transaction = group[2]
    fee_amount = send_transaction["fee"]
    send_asset = get_transfer_asset(send_transaction)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Full Limit Sell Order")


def _handle_algodex_full_buy_buy_side(group, exporter, txinfo):
    fee_amount = 0
    receive_transaction = group[2]
    receive_asset = get_transfer_asset(receive_transaction)

    app_transaction = group[0]
    n, d, _ = _get_order_details(app_transaction)

    send_asset = Algo((receive_asset.uint_amount * d) / n)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Full Limit Buy Order")


# AlgoDex whitepaper: Diagram 10
def _handle_algodex_full_sell_buy_side(group, exporter, txinfo):
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

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Full Limit Buy Order")


def _handle_algodex_full_sell_sell_side(group, exporter, txinfo):
    fee_amount = 0
    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    app_transaction = group[0]
    n, d, asset_id = _get_order_details(app_transaction)

    send_asset = Asset(asset_id, (receive_asset.uint_amount * n) / d)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Full Limit Sell Order")


# Undocumented
def _handle_algodex_market_order_buy_side(group, exporter, txinfo):
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

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Market Buy Order")


def _handle_algodex_market_order_sell_side(group, exporter, txinfo):
    fee_amount = 0
    app_transaction = group[0]
    n, d, asset_id = _get_order_details(app_transaction)

    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)
    send_asset = Asset(asset_id, (receive_asset.uint_amount * n) / d)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "AlgoDex Market Sell Order")


def _get_order_details(transaction):
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    # <n>-<d>-<min>-<asset_id>
    order_details = base64.b64decode(appl_args[1]).decode("utf-8").split("-")
    n = int(order_details[0])
    d = int(order_details[1])
    asset_id = int(order_details[3])
    return n, d, asset_id
