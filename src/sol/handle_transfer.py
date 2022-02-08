from common.make_tx import make_transfer_in_tx, make_transfer_out_tx
from sol.constants import (
    INSTRUCT_TRANSFERCHECK,
    INSTRUCT_TRANSFERCHECKED,
)
import sol.util_sol


def is_transfer(txinfo):
    instruction_types = txinfo.instruction_types
    log_instructions = txinfo.log_instructions

    # Check for transferCheck or transferChecked
    for instruction_type, program in instruction_types:
        if instruction_type in [INSTRUCT_TRANSFERCHECK, INSTRUCT_TRANSFERCHECKED]:
            return True

    if "Transfer" in log_instructions or ("transfer", "system") in instruction_types:
        # Verify no instructions except transfer or initialize/create/close account
        for instruction in log_instructions:
            if instruction not in ["Transfer", "InitializeAccount", "CloseAccount", "transfer", "system"]:
                return False
        return True

    return False


def handle_transfer(exporter, txinfo):
    txid = txinfo.txid
    transfers_in, transfers_out, _ = txinfo.transfers_net
    txinfo.fee = sol.util_sol.calculate_fee(txinfo)

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        amount, currency, _, dest = transfers_out[0]
        row = make_transfer_out_tx(txinfo, amount, currency, dest)
        exporter.ingest_row(row)
    elif len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency, _, _ = transfers_in[0]
        row = make_transfer_in_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    else:
        raise Exception("Bad condition in handle_transfer() txid=%s", txid)
