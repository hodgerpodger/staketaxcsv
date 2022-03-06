from algo import constants as co
from algo.asset import Algo
from algo.handle_simple import (
    handle_lp_add,
    handle_lp_remove,
    handle_participation_rewards,
    handle_swap, handle_unknown
)

WAGMISWAP_TRANSACTION_SWAP = "c3dhcA=="                  # "swap"
WAGMISWAP_TRANSACTION_LP_ADD = "YWRkLWxpcXVpZGl0eQ=="    # "add-liquidity"
WAGMISWAP_TRANSACTION_LP_REMOVE = "d2l0aGRyYXc="         # "withdraw"


def is_wagmiswap_transaction(group):
    length = len(group)
    if length < 2 or length > 4:
        return False

    last_tx = group[-1]
    if last_tx["tx-type"] != "appl":
        return False

    appl_args = last_tx[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if WAGMISWAP_TRANSACTION_SWAP in appl_args:
        return True

    if WAGMISWAP_TRANSACTION_LP_ADD in appl_args:
        return True

    if WAGMISWAP_TRANSACTION_LP_REMOVE in appl_args:
        return True

    return False


def handle_wagmiswap_transaction(group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    txinfo.comment = "Wagmiswap"
    appl_args = group[-1][co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if WAGMISWAP_TRANSACTION_SWAP in appl_args:
        handle_swap(group, exporter, txinfo)
    elif WAGMISWAP_TRANSACTION_LP_ADD in appl_args:
        handle_lp_add(group, exporter, txinfo)
    elif WAGMISWAP_TRANSACTION_LP_REMOVE in appl_args:
        handle_lp_remove(group, exporter, txinfo)
    else:
        handle_unknown(exporter, txinfo)
