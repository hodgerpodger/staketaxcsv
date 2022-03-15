from algo import constants as co
from algo.asset import Algo
from algo.handle_simple import (
    handle_lp_add,
    handle_lp_remove,
    handle_participation_rewards,
    handle_swap, handle_unknown
)

PACT_AMM_SYMBOL = "P"

PACT_TRANSACTION_SWAP = "U1dBUA=="           # "SWAP"
PACT_TRANSACTION_LP_ADD = "QURETElR"         # "ADDLIQ"
PACT_TRANSACTION_LP_REMOVE = "UkVNTElR"      # "REMLIQ"


def is_pact_transaction(group):
    length = len(group)
    if length < 2 or length > 4:
        return False

    last_tx = group[-1]
    if last_tx["tx-type"] != "appl":
        return False

    appl_args = last_tx[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if PACT_TRANSACTION_SWAP in appl_args:
        return True

    if PACT_TRANSACTION_LP_ADD in appl_args:
        return True

    if PACT_TRANSACTION_LP_REMOVE in appl_args:
        return True

    return False


def handle_pact_transaction(group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    txinfo.comment = "Pact"
    appl_args = group[-1][co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if PACT_TRANSACTION_SWAP in appl_args:
        handle_swap(group, exporter, txinfo)
    elif PACT_TRANSACTION_LP_ADD in appl_args:
        handle_lp_add(PACT_AMM_SYMBOL, group, exporter, txinfo)
    elif PACT_TRANSACTION_LP_REMOVE in appl_args:
        handle_lp_remove(PACT_AMM_SYMBOL, group, exporter, txinfo)
    else:
        handle_unknown(exporter, txinfo)
