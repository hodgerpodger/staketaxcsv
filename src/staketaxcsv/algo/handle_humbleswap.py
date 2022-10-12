import re

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import export_reward_tx
from staketaxcsv.algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_simple_lp_add_group,
    is_simple_lp_remove_group,
    is_simple_swap_group,
)
from staketaxcsv.algo.handle_simple import handle_participation_rewards, handle_unknown
from staketaxcsv.algo.util_algo import get_transaction_note, get_transfer_asset

HUMBLESWAP_AMM_SYMBOL = "HMB"

HUMBLESWAP_LP_TICKER = "HMBL2LT"

HUMBLESWAP_AMM_APPL_ARGS = set(["AA==", "Aw==", "AAAAAAAAAAA="])
HUMBLESWAP_FARM_APPL_ARGS = set(["AA==", "BA==", "AAAAAAAAAAA="])

reach_pattern = re.compile(r"^Reach \d+\.\d+\.\d+$")


def _is_humbleswap_amm_transaction(group):
    length = len(group)
    if length < 2 or length > 3:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    note = get_transaction_note(transaction)
    if note is None:
        return False

    if not reach_pattern.match(note):
        return False

    appl_args = set(transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"])
    return bool(appl_args & HUMBLESWAP_AMM_APPL_ARGS)


def _is_humbleswap_farm_transaction(group):
    if len(group) > 2:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    note = get_transaction_note(transaction)
    if note is None:
        return False

    if not reach_pattern.match(note):
        return False

    appl_args = set(transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"])
    return bool(appl_args & HUMBLESWAP_FARM_APPL_ARGS)


def is_humbleswap_transaction(group):
    return _is_humbleswap_amm_transaction(group) or _is_humbleswap_farm_transaction(group)


def handle_humbleswap_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    txinfo.comment = "Humbleswap"
    if is_simple_swap_group(wallet_address, group):
        handle_swap(group, exporter, txinfo)
    elif is_simple_lp_add_group(wallet_address, group):
        handle_lp_add(HUMBLESWAP_AMM_SYMBOL, group, exporter, txinfo)
    elif is_simple_lp_remove_group(wallet_address, group):
        handle_lp_remove(HUMBLESWAP_AMM_SYMBOL, group, exporter, txinfo)
    elif _is_humbleswap_farm_transaction(group):
        _handle_humbleswap_farm(group, exporter, txinfo)
    else:
        handle_unknown(exporter, txinfo)


def _handle_humbleswap_farm(group, exporter, txinfo):
    fee_amount = 0
    app_transaction = group[-1]

    inner_transactions = app_transaction.get("inner-txns", [])
    for transaction in inner_transactions:
        txtype = transaction["tx-type"]
        if txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER or txtype == co.TRANSACTION_TYPE_PAYMENT:
            reward = get_transfer_asset(transaction)
            if not reward.zero() and reward.ticker != HUMBLESWAP_LP_TICKER:
                export_reward_tx(exporter, txinfo, reward, fee_amount)
