import base64
import json
import re

from algo import constants as co
from algo.asset import Algo, Asset
from common.make_tx import make_swap_tx

# For reference check the whitepaper appendix:
# https://github.com/algodex/algodex-public-documents/blob/master/Algodex%20Whitepaper%201.0.pdf

APPLICATION_ID_ALGODEX_BUY = 354073718
APPLICATION_ID_ALGODEX_SELL = 354073834

ACTION_TYPE_OPEN = "open"
ACTION_TYPE_CLOSE = "close"
ACTION_TYPE_EXECUTE_PARTIAL = "execute_partial"
ACTION_TYPE_EXECUTE_FULL = "execute_full"

ALGODEX_ACTION_TYPES = [
    ACTION_TYPE_OPEN,
    ACTION_TYPE_CLOSE,
    ACTION_TYPE_EXECUTE_PARTIAL,
    ACTION_TYPE_EXECUTE_FULL
]

ORDER_TYPE_BUY = "buy"
ORDER_TYPE_SELL = "sell"


order_pattern = re.compile(r"^\w+-\d+-\[(\w+)\]_\[\w+\]")


def is_algodex_transaction(wallet_address, group):
    length = len(group)
    if length < 1 or length > 4:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
        if app_id != APPLICATION_ID_ALGODEX_BUY and app_id != APPLICATION_ID_ALGODEX_SELL:
            return False

    if "note" not in transaction:
        return False

    if len(transaction["note"]) < len(wallet_address):
        return False

    note = json.loads(base64.b64decode(transaction["note"]))
    key = next(iter(note))

    match = order_pattern.match(key)
    if not match:
        return False

    action_type = match.group(1)
    if action_type not in ALGODEX_ACTION_TYPES:
        return False

    return True


def handle_algodex_transaction(group, exporter, txinfo):
    transaction = group[0]
    note = json.loads(base64.b64decode(transaction["note"]))
    key = next(iter(note))
    order_details = note.get(key)
    order_type = order_details["escrowOrderType"]
    if ACTION_TYPE_EXECUTE_PARTIAL in key:
        if order_type == ORDER_TYPE_BUY:
            _handle_algodex_partial_buy(group, exporter, txinfo, order_details)
        else:
            _handle_algodex_partial_sell(group, exporter, txinfo)
    elif ACTION_TYPE_EXECUTE_FULL in key:
        if order_type == ORDER_TYPE_BUY:
            _handle_algodex_full_buy(group, exporter, txinfo, order_details)
        else:
            _handle_algodex_full_sell(group, exporter, txinfo)
    # Ignore open and close orders


# AlgoDex whitepaper: Diagram 7
def _handle_algodex_partial_buy(group, exporter, txinfo, order):
    receive_transaction = group[1]
    receive_amount = receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"]
    receive_asset = Asset(
        receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"],
        receive_amount)

    send_amount = receive_amount * order["price"]
    send_asset = Algo(send_amount)

    txinfo.comment = "AlgoDex Partial Order"

    row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    exporter.ingest_row(row)


# AlgoDex whitepaper: Diagram 11
def _handle_algodex_partial_sell(group, exporter, txinfo):
    send_transaction = group[1]
    fee_amount = send_transaction["fee"]
    send_asset = Algo(send_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"])

    receive_transaction = group[2]
    receive_asset = Asset(
        receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"],
        receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"])

    fee_transaction = group[3]
    fee_amount += fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "AlgoDex Partial Order"

    row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    exporter.ingest_row(row)


# AlgoDex whitepaper: Diagram 6
def _handle_algodex_full_buy(group, exporter, txinfo, order):
    receive_transaction = group[2]
    receive_amount = receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"]
    receive_asset = Asset(
        receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"],
        receive_amount)

    send_amount = receive_amount * order["price"]
    send_asset = Algo(send_amount)

    txinfo.comment = "AlgoDex Full Order"

    row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    exporter.ingest_row(row)


# AlgoDex whitepaper: Diagram 10
def _handle_algodex_full_sell(group, exporter, txinfo):
    send_transaction = group[1]
    fee_amount = send_transaction["fee"]
    send_asset = Algo(send_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"])

    receive_transaction = group[2]
    receive_asset = Asset(
        receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"],
        receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"])

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "AlgoDex Full Order"

    row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    exporter.ingest_row(row)
