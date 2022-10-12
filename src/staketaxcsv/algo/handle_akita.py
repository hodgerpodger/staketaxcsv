from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.export_tx import export_swap_tx
from staketaxcsv.algo.handle_simple import handle_participation_rewards

APPLICATION_ID_AKITA_SWAP = 537279393


def is_akita_swap_transaction(group):
    if len(group) != 3:
        return False

    if (group[0]["tx-type"] != co.TRANSACTION_TYPE_ASSET_TRANSFER
            or group[1]["tx-type"] != co.TRANSACTION_TYPE_ASSET_TRANSFER
            or group[2]["tx-type"] != co.TRANSACTION_TYPE_APP_CALL):
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

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "Akita Migration Swap")
