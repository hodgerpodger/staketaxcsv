import urllib.parse
from datetime import datetime

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.util import b64_decode_ascii
from staketaxcsv.common.TxInfo import TxInfo


def get_transaction_txinfo(wallet_address, elem):
    txid = elem["id"]

    timestamp = datetime.utcfromtimestamp(elem["round-time"]).strftime('%Y-%m-%d %H:%M:%S')
    fee = Algo(0)

    url = "https://explorer.perawallet.app/tx/{}".format(urllib.parse.quote(txid))

    return TxInfo(txid, timestamp, fee, fee.ticker, wallet_address, co.EXCHANGE_ALGORAND_BLOCKCHAIN, url)


def get_transaction_note(transaction, size=0):
    if "note" not in transaction:
        return ""

    note = b64_decode_ascii(transaction["note"])
    end = size or len(note)

    return note[:end]


def get_transfer_receiver(transaction):
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        return transaction[co.TRANSACTION_KEY_PAYMENT]["receiver"]
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]

    return None


def get_transfer_sender(transaction):
    return transaction["sender"]


def is_transfer_receiver(wallet_address, transaction):
    return wallet_address == get_transfer_receiver(transaction)


def is_transaction_sender(wallet_address, transaction):
    return wallet_address == get_transfer_sender(transaction)


def is_transfer_receiver_non_zero_asset(wallet_address, transaction):
    if not is_transfer_receiver(wallet_address, transaction):
        return False
    asset = get_transfer_asset(transaction)
    return asset is not None and not asset.zero()


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


def get_transfer_asset_id(transaction):
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        return 0
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"]
    else:
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


def generate_inner_transfer_assets(transaction, asset_map={}, filter=None):
    inner_transactions = transaction.get("inner-txns", [])
    for tx in inner_transactions:
        if is_transfer(tx):
            if filter is None or filter(tx):
                yield get_transfer_asset(tx, asset_map)
        elif is_app_call(tx):
            yield from generate_inner_transfer_assets(tx, asset_map, filter)


def get_inner_transfer_asset(transaction, asset_map={}, filter=None):
    inner_transactions = transaction.get("inner-txns", [])
    for tx in inner_transactions:
        txtype = tx["tx-type"]
        if is_transfer(tx):
            if filter is None or filter(tx):
                return get_transfer_asset(tx, asset_map)
        elif txtype == co.TRANSACTION_TYPE_APP_CALL and "inner-txns" in tx:
            asset = get_inner_transfer_asset(tx, asset_map, filter)
            if asset is not None:
                return asset

    return None


def get_inner_transfer_count(transaction, depth=1):
    if depth == 0:
        return 0

    inner_transactions = transaction.get("inner-txns", [])
    count = 0
    for tx in inner_transactions:
        if is_transfer(tx):
            count += 1
        elif tx["tx-type"] == co.TRANSACTION_TYPE_APP_CALL:
            count += get_inner_transfer_count(tx, depth - 1)

    return count


def is_asset_optin(transaction):
    if is_asa_transfer(transaction) and get_transfer_sender(transaction) == get_transfer_receiver(transaction):
        return True

    inner_transactions = transaction.get("inner-txns", [])
    if not inner_transactions:
        return False

    return all([is_asset_optin(tx) for tx in inner_transactions])


def is_transfer(transaction):
    txtype = transaction["tx-type"]
    return txtype == co.TRANSACTION_TYPE_PAYMENT or txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER


def is_algo_transfer(transaction):
    return transaction["tx-type"] == co.TRANSACTION_TYPE_PAYMENT


def is_asa_transfer(transaction):
    return transaction["tx-type"] == co.TRANSACTION_TYPE_ASSET_TRANSFER


def is_app_call(transaction, app_id=None, app_args=None, foreign_app=None):
    if transaction["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return False

    if isinstance(app_id, list) and transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"] not in app_id:
        return False
    elif isinstance(app_id, int) and transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"] != app_id:
        return False

    if (isinstance(foreign_app, list)
            and not any(app in transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"] for app in foreign_app)):
        return False
    if isinstance(foreign_app, int) and foreign_app not in transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]:
        return False

    if isinstance(app_args, str) and app_args not in get_app_args(transaction):
        return False
    if (isinstance(app_args, list) and not any(arg in get_app_args(transaction) for arg in app_args)):
        return False

    return True


def is_app_optin(transaction):
    if transaction["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return False

    return transaction[co.TRANSACTION_KEY_APP_CALL].get("on-completion") == "optin"


def is_app_clear(transaction):
    if transaction["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return False

    return transaction[co.TRANSACTION_KEY_APP_CALL].get("on-completion") == "clear"


def get_fee_amount(wallet_address, group):
    return sum([transaction["fee"] for transaction in group if wallet_address == transaction["sender"]])


def get_app_args(transaction):
    if transaction["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return []

    return transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]


def get_app_local_state_delta_value(transaction, address, key):
    if transaction["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return None

    local_state_delta = transaction.get("local-state-delta", [])
    for account_state_delta in local_state_delta:
        if account_state_delta["address"] == address:
            for kv in account_state_delta["delta"]:
                if kv["key"] == key:
                    return kv["value"]

    return None


def get_app_global_state_delta_value(transaction, key):
    if transaction["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return None

    global_state_delta = transaction.get("global-state-delta", [])
    for kv in global_state_delta:
        if kv["key"] == key:
            return kv["value"]

    return None
