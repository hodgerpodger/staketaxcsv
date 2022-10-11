import base64

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Asset


def get_transaction_note(transaction):
    if "note" not in transaction:
        return None

    try:
        note = base64.b64decode(transaction["note"]).decode("utf-8")
    except Exception:
        return None

    return note


def get_transfer_receiver(transaction):
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        return transaction[co.TRANSACTION_KEY_PAYMENT]["receiver"]
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]

    return None


def get_transfer_asset(transaction, asset_map={}):
    amount = 0
    asset_id = 0
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        amount = transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        amount = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"]
        asset_id = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"]

    return Asset(asset_map.get(asset_id, asset_id), amount)


def get_transfer_close_to_asset(transaction, asset_map={}):
    amount = 0
    asset_id = 0
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        amount = transaction[co.TRANSACTION_KEY_PAYMENT]["close-amount"]
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        amount = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["close-amount"]
        asset_id = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"]

    return Asset(asset_map.get(asset_id, asset_id), amount)


def get_inner_transfer_asset(transaction, asset_map={}):
    inner_transactions = transaction.get("inner-txns", [])
    for tx in inner_transactions:
        txtype = tx["tx-type"]
        if txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER or txtype == co.TRANSACTION_TYPE_PAYMENT:
            return get_transfer_asset(tx, asset_map)
        elif txtype == co.TRANSACTION_TYPE_APP_CALL and "inner-txns" in tx:
            asset = get_inner_transfer_asset(tx, asset_map)
            if asset is not None:
                return asset

    return None
