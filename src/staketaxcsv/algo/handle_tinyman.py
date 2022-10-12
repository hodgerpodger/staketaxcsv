from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import (
    export_income_tx,
    export_lp_deposit_tx,
    export_lp_withdraw_tx,
    export_reward_tx,
    export_swap_tx,
)
from staketaxcsv.algo.handle_simple import handle_participation_rewards, handle_unknown
from staketaxcsv.algo.util_algo import get_transfer_asset

APPLICATION_ID_TINYMAN_v10 = 350338509
APPLICATION_ID_TINYMAN_v11 = 552635992
APPLICATION_ID_TINYMAN_STAKING = 649588853

COMMENT_TINYMAN = "Tinyman"

TINYMAN_AMM_SYMBOL = "TM"

TINYMAN_TRANSACTION_SWAP = "c3dhcA=="           # "swap"
TINYMAN_TRANSACTION_REDEEM = "cmVkZWVt"         # "redeem"
TINYMAN_TRANSACTION_LP_ADD = "bWludA=="         # "mint"
TINYMAN_TRANSACTION_LP_REMOVE = "YnVybg=="      # "burn"
TINYMAN_TRANSACTION_CLAIM = "Y2xhaW0="          # "claim"


def _is_tinyman_amm_transaction(group, required_length, appl_arg):
    if len(group) != required_length:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in [APPLICATION_ID_TINYMAN_v10, APPLICATION_ID_TINYMAN_v11]:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return appl_arg in appl_args


def _is_tinyman_swap(group):
    return _is_tinyman_amm_transaction(group, 4, TINYMAN_TRANSACTION_SWAP)


def _is_tinyman_redeem(group):
    return _is_tinyman_amm_transaction(group, 3, TINYMAN_TRANSACTION_REDEEM)


def _is_tinyman_lp_add(group):
    return _is_tinyman_amm_transaction(group, 5, TINYMAN_TRANSACTION_LP_ADD)


def _is_tinyman_lp_remove(group):
    return _is_tinyman_amm_transaction(group, 5, TINYMAN_TRANSACTION_LP_REMOVE)


def _is_tinyman_claim(group):
    if len(group) != 2:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id != APPLICATION_ID_TINYMAN_STAKING:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return TINYMAN_TRANSACTION_CLAIM in appl_args


def is_tinyman_transaction(group):
    return (_is_tinyman_swap(group)
                or _is_tinyman_redeem(group)
                or _is_tinyman_lp_add(group)
                or _is_tinyman_lp_remove(group)
                or _is_tinyman_claim(group))


def handle_tinyman_transaction(group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    if _is_tinyman_swap(group):
        _handle_tinyman_swap(group, exporter, txinfo)

    elif _is_tinyman_redeem(group):
        _handle_tinyman_redeem(group, exporter, txinfo)

    elif _is_tinyman_lp_add(group):
        _handle_tinyman_lp_add(group, exporter, txinfo)

    elif _is_tinyman_lp_remove(group):
        _handle_tinyman_lp_remove(group, exporter, txinfo)

    elif _is_tinyman_claim(group):
        _handle_tinyman_claim(group, exporter, txinfo)

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

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_TINYMAN)


def _handle_tinyman_redeem(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"] + fee_transaction["fee"]

    receive_transaction = group[2]
    receive_asset = get_transfer_asset(receive_transaction)

    export_income_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_TINYMAN)


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
        exporter, txinfo, TINYMAN_AMM_SYMBOL, send_asset_1, send_asset_2, lp_asset, fee_amount, COMMENT_TINYMAN)


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
        exporter, txinfo, TINYMAN_AMM_SYMBOL, lp_asset, receive_asset_1, receive_asset_2, fee_amount, COMMENT_TINYMAN)


def _handle_tinyman_claim(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]

    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    export_reward_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_TINYMAN)
