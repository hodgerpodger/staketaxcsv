from algo import constants as co
from algo.asset import Algo
from algo.export_tx import export_income_tx, export_lp_deposit_tx, export_lp_withdraw_tx, export_swap_tx
from algo.handle_simple import handle_participation_rewards, handle_unknown
from algo.util_algo import get_transfer_asset

APPLICATION_ID_TINYMAN_v10 = 350338509
APPLICATION_ID_TINYMAN_v11 = 552635992

TINYMAN_AMM_SYMBOL = "TM"

TINYMAN_TRANSACTION_SWAP = "c3dhcA=="           # "swap"
TINYMAN_TRANSACTION_REDEEM = "cmVkZWVt"         # "redeem"
TINYMAN_TRANSACTION_LP_ADD = "bWludA=="         # "mint"
TINYMAN_TRANSACTION_LP_REMOVE = "YnVybg=="      # "burn"


def is_tinyman_transaction(group):
    length = len(group)
    if length < 3 or length > 5:
        return False

    if group[1]["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = group[1][co.TRANSACTION_KEY_APP_CALL]["application-id"]

    return (app_id == APPLICATION_ID_TINYMAN_v10 or app_id == APPLICATION_ID_TINYMAN_v11)


def handle_tinyman_transaction(group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    appl_args = group[1][co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if TINYMAN_TRANSACTION_SWAP in appl_args:
        _handle_tinyman_swap(group, exporter, txinfo)
    elif TINYMAN_TRANSACTION_REDEEM in appl_args:
        _handle_tinyman_redeem(group, exporter, txinfo)
    elif TINYMAN_TRANSACTION_LP_ADD in appl_args:
        _handle_tinyman_lp_add(group, exporter, txinfo)
    elif TINYMAN_TRANSACTION_LP_REMOVE in appl_args:
        _handle_tinyman_lp_remove(group, exporter, txinfo)
    else:
        handle_unknown(exporter, txinfo)


def _handle_tinyman_swap(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

    send_transaction = group[2]
    fee_amount += send_transaction["fee"]
    send_asset = get_transfer_asset(send_transaction)

    receive_transaction = group[3]
    receive_asset = get_transfer_asset(receive_transaction)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "Tinyman")


def _handle_tinyman_redeem(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

    receive_transaction = group[2]
    receive_asset = get_transfer_asset(receive_transaction)

    export_income_tx(exporter, txinfo, receive_asset, fee_amount, "Tinyman")


def _handle_tinyman_lp_add(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

    send_transaction = group[2]
    fee_amount += send_transaction["fee"]
    send_asset_1 = get_transfer_asset(send_transaction)

    send_transaction = group[3]
    fee_amount += send_transaction["fee"]
    send_asset_2 = get_transfer_asset(send_transaction)

    receive_transaction = group[4]
    lp_asset = get_transfer_asset(receive_transaction)

    export_lp_deposit_tx(
        exporter, txinfo, TINYMAN_AMM_SYMBOL, send_asset_1, send_asset_2, lp_asset, fee_amount, "Tinyman")


def _handle_tinyman_lp_remove(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

    receive_transaction = group[2]
    receive_asset_1 = get_transfer_asset(receive_transaction)

    receive_transaction = group[3]
    receive_asset_2 = get_transfer_asset(receive_transaction)

    send_transaction = group[4]
    fee_amount += send_transaction["fee"]
    lp_asset = get_transfer_asset(send_transaction)

    export_lp_withdraw_tx(
        exporter, txinfo, TINYMAN_AMM_SYMBOL, lp_asset, receive_asset_1, receive_asset_2, fee_amount, "Tinyman")
