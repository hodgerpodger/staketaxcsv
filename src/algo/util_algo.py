import base64

from algo import constants as co
from algo.asset import Asset


def get_transaction_note(transaction):
    if "note" not in transaction:
        return None

    try:
        note = base64.b64decode(transaction["note"]).decode("utf-8")
    except Exception:
        return None

    return note


def get_transfer_asset(transaction, asset_map={}):
    amount = 0
    asset_id = 0
    txtype = transaction["tx-type"]
    if txtype == "pay":
        amount = transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]
    elif txtype == "axfer":
        amount = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"]
        asset_id = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"]

    return Asset(asset_map.get(asset_id, asset_id), amount)
