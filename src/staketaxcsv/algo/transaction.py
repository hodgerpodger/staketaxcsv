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


def is_transfer_receiver(wallet_address, transaction):
    return wallet_address == get_transfer_receiver(transaction)


def generate_transfer_accounts(transaction):
    yield transaction["sender"]

    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        details = transaction[co.TRANSACTION_KEY_PAYMENT]
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        details = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    else:
        return

    yield details["receiver"]

    close_to = details.get("close-to", details.get("close-remainder-to", None))
    if close_to is not None:
        yield close_to


def is_transfer_participant(wallet_address, transaction):
    return wallet_address in generate_transfer_accounts(transaction)


def get_transfer_asset(transaction, asset_map={}):
    amount = 0
    asset_id = 0
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        amount = transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        amount = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"]
        asset_id = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"]
    else:
        return None

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


def get_inner_transfer_asset(transaction, asset_map={}, filter=None):
    inner_transactions = transaction.get("inner-txns", [])
    for tx in inner_transactions:
        txtype = tx["tx-type"]
        if txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER or txtype == co.TRANSACTION_TYPE_PAYMENT:
            if filter is None or filter(tx):
                return get_transfer_asset(tx, asset_map)
        elif txtype == co.TRANSACTION_TYPE_APP_CALL and "inner-txns" in tx:
            asset = get_inner_transfer_asset(tx, asset_map, filter)
            if asset is not None:
                return asset

    return None


def is_asset_optin(transaction):
    return (transaction["tx-type"] == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and transaction["sender"] == transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"])


def is_transfer(transaction):
    txtype = transaction["tx-type"]
    return txtype == co.TRANSACTION_TYPE_PAYMENT or txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER


def is_app_call(transaction, app_id=None, app_args=None, foreign_app=None):
    if transaction["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return False

    if isinstance(app_id, list) and transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"] not in app_id:
        return False
    elif isinstance(app_id, str) and transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"] != app_id:
        return False

    if (isinstance(foreign_app, list)
            and not any(app in transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"] for app in foreign_app)):
        return False
    if isinstance(foreign_app, str) and foreign_app not in transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]:
        return False

    if isinstance(app_args, str) and app_args not in transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]:
        return False

    return True


def get_fee_amount(wallet_address, group):
    return sum([transaction["fee"] for transaction in group if wallet_address == transaction["sender"]])
