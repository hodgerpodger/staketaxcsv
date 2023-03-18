import re

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import export_participation_rewards, export_reward_tx, export_unknown
from staketaxcsv.algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_lp_add_group,
    is_lp_remove_group,
    is_swap_group,
)
from staketaxcsv.algo.transaction import get_transaction_note, get_transfer_asset, is_transfer

APPLICATION_ID_HUMBLESWAP_PROXY = 818079669

HUMBLESWAP_LP_TICKER = "HMBL2LT"

HUMBLESWAP_AMM_APPL_ARGS = set(["AA==", "Aw==", "AAAAAAAAAAA="])
HUMBLESWAP_FARM_APPL_ARGS = set(["AA==", "BA==", "AAAAAAAAAAA="])

HUMBLESWAP_TRANSACTION_PROXY_SWAP = "NS1KHQ=="

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
    if not note:
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
    if not note:
        return False

    if not reach_pattern.match(note):
        return False

    appl_args = set(transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"])
    return bool(appl_args & HUMBLESWAP_FARM_APPL_ARGS)


def is_humbleswap_transaction(group):
    return _is_humbleswap_amm_transaction(group) or _is_humbleswap_farm_transaction(group)


def handle_humbleswap_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    export_participation_rewards(reward, exporter, txinfo)

    txinfo.comment = "Humbleswap"
    if is_swap_group(wallet_address, group):
        handle_swap(wallet_address, group, exporter, txinfo)
    elif is_lp_add_group(wallet_address, group):
        handle_lp_add(group, exporter, txinfo)
    elif is_lp_remove_group(wallet_address, group):
        handle_lp_remove(group, exporter, txinfo)
    elif _is_humbleswap_farm_transaction(group):
        _handle_humbleswap_farm(group, exporter, txinfo)
    else:
        export_unknown(exporter, txinfo)


def _handle_humbleswap_farm(group, exporter, txinfo):
    fee_amount = 0
    app_transaction = group[-1]

    inner_transactions = app_transaction.get("inner-txns", [])
    for transaction in inner_transactions:
        if is_transfer(transaction):
            reward = get_transfer_asset(transaction)
            if not reward.zero() and reward.ticker != HUMBLESWAP_LP_TICKER:
                export_reward_tx(exporter, txinfo, reward, fee_amount)
