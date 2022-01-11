from terra import util_terra
from terra.constants import CUR_AUST, CUR_UST
from terra.handle_simple import handle_unknown
from terra.make_tx import make_swap_tx_terra


def _exchange_rate(ust, aust):
    return ust / aust


def handle_anchor_earn_deposit(exporter, elem, txinfo):
    from_contract = util_terra._event_with_action(elem, "from_contract", "deposit_stable")

    if from_contract is None:
        # some older transactions for some reason missing from LCD and this key in FCD
        handle_unknown(exporter, txinfo)
        return

    deposit_amount = from_contract["deposit_amount"][0]
    mint_amount = from_contract["mint_amount"][0]
    ust = util_terra._float_amount(deposit_amount, CUR_UST)
    aust = util_terra._float_amount(mint_amount, CUR_AUST)

    txinfo.comment = "earn_deposit [1 aUST = {} UST]".format(_exchange_rate(ust, aust))
    row = make_swap_tx_terra(txinfo, ust, CUR_UST, aust, CUR_AUST)
    exporter.ingest_row(row)


def handle_anchor_earn_withdraw(exporter, elem, txinfo):
    from_contract = util_terra._event_with_action(elem, "from_contract", "redeem_stable")

    if from_contract is None:
        # some older transactions for some reason missing from LCD and this key in FCD
        handle_unknown(exporter, txinfo)
        return

    redeem_amount = from_contract["redeem_amount"][0]
    burn_amount = from_contract["burn_amount"][0]
    ust = util_terra._float_amount(redeem_amount, CUR_UST)
    aust = util_terra._float_amount(burn_amount, CUR_AUST)

    txinfo.comment = "earn_withdraw [1 aUST = {} UST]".format(_exchange_rate(ust, aust))
    row = make_swap_tx_terra(txinfo, aust, CUR_AUST, ust, CUR_UST)
    exporter.ingest_row(row)
