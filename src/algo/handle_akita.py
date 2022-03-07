from algo import constants as co
from algo.asset import Algo, Asset
from algo.handle_simple import handle_participation_rewards
from common.make_tx import make_reward_tx, make_swap_tx

APPLICATION_ID_AKITA_SWAP = 537279393


def is_akita_swap_transaction(group):
    if len(group) != 3:
        return False

    if (group[0]["tx-type"] != "axfer"
            or group[1]["tx-type"] != "axfer"
            or group[2]["tx-type"] != "appl"):
        return False

    app_transaction = group[2]
    app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id != APPLICATION_ID_AKITA_SWAP:
        return False

    if "inner-txns" not in app_transaction:
        return False

    if len(app_transaction["inner-txns"]) != 1:
        return False

    return True


def handle_akita_swap_transaction(group, exporter, txinfo):
    optin_transaction = group[0]
    fee_amount = optin_transaction["fee"]

    reward = Algo(optin_transaction["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    send_transaction = group[1]
    fee_amount += send_transaction["fee"]
    asset_id = send_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"]
    amount = send_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"]
    send_asset = Asset(asset_id, amount)

    app_transaction = group[2]
    fee_amount += app_transaction["fee"]
    receive_transaction = app_transaction["inner-txns"][0]
    asset_id = receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["asset-id"]
    amount = receive_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["amount"]
    receive_asset = Asset(asset_id, amount)

    fee = Algo(fee_amount)
    txinfo.comment = "Akita Migration Swap"

    row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    row.fee = fee.amount
    exporter.ingest_row(row)
