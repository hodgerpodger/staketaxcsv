from algo import constants as co
from algo.asset import Algo
from algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_simple_lp_add_group,
    is_simple_lp_remove_group,
    is_simple_swap_group
)
from algo.handle_simple import handle_participation_rewards, handle_unknown

HUMBLESWAP_AMM_SYMBOL = "HMB"

HUMBLESWAP_NOTE = "UmVhY2ggMC4xLjg="  # Reach 0.1.8


def is_humbleswap_transaction(group):
    length = len(group)
    if length < 2:
        return False

    last_tx = group[-1]
    if last_tx["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return False

    # TODO find a better solution when they release their SDK
    note = last_tx.get("note")
    if note == HUMBLESWAP_NOTE:
        return True

    return False


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
    else:
        handle_unknown(exporter, txinfo)
