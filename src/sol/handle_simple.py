from common.ExporterTypes import (
    TX_TYPE_SOL_STAKING_CREATE,
    TX_TYPE_SOL_STAKING_DEACTIVATE,
    TX_TYPE_SOL_STAKING_SPLIT,
    TX_TYPE_SOL_STAKING_WITHDRAW,
    TX_TYPE_STAKING_DELEGATE,
)
from common.make_tx import make_simple_tx, make_unknown_tx, make_unknown_tx_with_transfer, make_spend_tx
from sol.constants import (
    INSTRUCTION_TYPE_CREATE_ACCOUNT_WITH_SEED,
    INSTRUCTION_TYPE_DEACTIVATE,
    INSTRUCTION_TYPE_DELEGATE,
    INSTRUCTION_TYPE_INITIALIZE,
    INSTRUCTION_TYPE_SPLIT,
    INSTRUCTION_TYPE_WITHDRAW,
    PROGRAM_STAKE,
    PROGRAM_SYSTEM,
)
import sol.util_sol

SIMPLE_TXS = {
    (INSTRUCTION_TYPE_DEACTIVATE, PROGRAM_STAKE): TX_TYPE_SOL_STAKING_DEACTIVATE,
    (INSTRUCTION_TYPE_WITHDRAW, PROGRAM_STAKE): TX_TYPE_SOL_STAKING_WITHDRAW,
    (INSTRUCTION_TYPE_SPLIT, PROGRAM_STAKE): TX_TYPE_SOL_STAKING_SPLIT,
    (INSTRUCTION_TYPE_DELEGATE, PROGRAM_STAKE): TX_TYPE_STAKING_DELEGATE,
    (INSTRUCTION_TYPE_INITIALIZE, PROGRAM_STAKE): TX_TYPE_SOL_STAKING_CREATE,
    (INSTRUCTION_TYPE_CREATE_ACCOUNT_WITH_SEED, PROGRAM_SYSTEM): TX_TYPE_SOL_STAKING_CREATE,
}


def is_simple_tx(txinfo):
    instruction_types = txinfo.instruction_types

    for instruction_type, program in instruction_types:
        if (instruction_type, program) in SIMPLE_TXS:
            return True

    return False


def handle_simple_tx(exporter, txinfo):
    instruction_types = txinfo.instruction_types

    for instruction_type, program in reversed(instruction_types):
        key = (instruction_type, program)
        if key in SIMPLE_TXS:
            tx_type = SIMPLE_TXS[key]
            break
    _handle_generic(exporter, txinfo, tx_type)


def handle_unknown(exporter, txinfo):
    txinfo.fee = sol.util_sol.calculate_fee(txinfo)
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)


def _handle_generic(exporter, txinfo, tx_type):
    txinfo.fee = sol.util_sol.calculate_fee(txinfo)

    row = make_spend_tx(txinfo, txinfo.fee, txinfo.fee_currency)
    row.fee = ""
    row.fee_currency = ""
    row.comment = "fee for {}".format(tx_type)
    exporter.ingest_row(row)


def handle_unknown_detect_transfers(exporter, txinfo):
    transfers_net_in, transfers_net_out, _ = txinfo.transfers_net

    if len(transfers_net_in) == 0 and len(transfers_net_out) == 0:
        handle_unknown(exporter, txinfo)
    elif len(transfers_net_in) == 1 and len(transfers_net_out) == 1:
        sent_amount, sent_currency, _, _ = transfers_net_out[0]
        received_amount, received_currency, _, _ = transfers_net_in[0]

        row = make_unknown_tx_with_transfer(
            txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        i = 0
        for sent_amount, sent_currency, _, _ in transfers_net_out:
            row = make_unknown_tx_with_transfer(
                txinfo, sent_amount, sent_currency, "", "", empty_fee=(i > 0), z_index=i
            )
            exporter.ingest_row(row)
            i += 1
        for received_amount, received_currency, _, _ in transfers_net_in:
            row = make_unknown_tx_with_transfer(
                txinfo, "", "", received_amount, received_currency, empty_fee=(i > 0), z_index=i
            )
            exporter.ingest_row(row)
            i += 1
