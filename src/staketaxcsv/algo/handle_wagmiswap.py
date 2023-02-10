from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import export_participation_rewards, export_unknown
from staketaxcsv.algo.handle_amm import handle_lp_add, handle_lp_remove, handle_swap
from staketaxcsv.algo.transaction import is_app_call

APPLICATION_ID_WAGMISWAP_ORDER_ROUTER = [
    605315844,  # ALGO-ARCC
    605328585,  # ARCC-YLDY
]

WAGMISWAP_TRANSACTION_SWAP = "c3dhcA=="                  # "swap"
WAGMISWAP_TRANSACTION_LP_ADD = "YWRkLWxpcXVpZGl0eQ=="    # "add-liquidity"
WAGMISWAP_TRANSACTION_LP_REMOVE = "d2l0aGRyYXc="         # "withdraw"


def is_wagmiswap_transaction(group):
    length = len(group)
    if length < 2:
        return False

    return is_app_call(group[-1], APPLICATION_ID_WAGMISWAP_ORDER_ROUTER,
        [WAGMISWAP_TRANSACTION_SWAP, WAGMISWAP_TRANSACTION_LP_ADD, WAGMISWAP_TRANSACTION_LP_REMOVE])


def handle_wagmiswap_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    export_participation_rewards(reward, exporter, txinfo)

    txinfo.comment = "Wagmiswap"
    appl_args = group[-1][co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if WAGMISWAP_TRANSACTION_SWAP in appl_args:
        handle_swap(wallet_address, group, exporter, txinfo)
    elif WAGMISWAP_TRANSACTION_LP_ADD in appl_args:
        handle_lp_add(group, exporter, txinfo)
    elif WAGMISWAP_TRANSACTION_LP_REMOVE in appl_args:
        handle_lp_remove(group, exporter, txinfo)
    else:
        export_unknown(exporter, txinfo)
