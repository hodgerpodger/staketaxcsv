from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import export_participation_rewards, export_unknown
from staketaxcsv.algo.handle_amm import handle_lp_add, handle_lp_remove, handle_swap
from staketaxcsv.algo.transaction import is_app_call

PACT_TRANSACTION_SWAP = "U1dBUA=="           # "SWAP"
PACT_TRANSACTION_LP_ADD = "QURETElR"         # "ADDLIQ"
PACT_TRANSACTION_LP_REMOVE = "UkVNTElR"      # "REMLIQ"


def is_pact_transaction(group):
    length = len(group)
    if length < 2:
        return False

    return is_app_call(group[-1], app_args=[PACT_TRANSACTION_SWAP,
                                            PACT_TRANSACTION_LP_ADD,
                                            PACT_TRANSACTION_LP_REMOVE])


def handle_pact_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    export_participation_rewards(reward, exporter, txinfo)

    txinfo.comment = "Pact"
    appl_args = group[-1][co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if PACT_TRANSACTION_SWAP in appl_args:
        handle_swap(wallet_address, group, exporter, txinfo)
    elif PACT_TRANSACTION_LP_ADD in appl_args:
        handle_lp_add(group, exporter, txinfo)
    elif PACT_TRANSACTION_LP_REMOVE in appl_args:
        handle_lp_remove(group, exporter, txinfo)
    else:
        export_unknown(exporter, txinfo)
