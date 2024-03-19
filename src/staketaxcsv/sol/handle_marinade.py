from staketaxcsv.common.make_tx import make_swap_tx
from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers, _handle_generic
from staketaxcsv.sol.constants import (
    INSTRUCTION_TYPE_INITIALIZE, PROGRAM_STAKE, MARINADE_STAKER_AUTHORITY)
from staketaxcsv.common.ExporterTypes import TX_TYPE_SOL_STAKING_CREATE


def handle_marinade(exporter, txinfo):
    txinfo.comment = "marinade_finance"

    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if len(transfers_in) == 1 and len(transfers_out) == 1 and len(transfers_unknown) == 0:
        received_amount, received_currency, _, _ = transfers_in[0]
        sent_amount, sent_currency, _, _ = transfers_out[0]
        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo)


def is_marinade_native_staking_create_tx(txinfo):
    instructions = txinfo.instructions

    for instruction in instructions:
        parsed = instruction.get("parsed", None)
        instruction_type = parsed.get("type", None) if (parsed and type(parsed) is dict) else None
        program = instruction.get("program")

        if (
            program == PROGRAM_STAKE
            and instruction_type == INSTRUCTION_TYPE_INITIALIZE
            and parsed.get("info", {}).get("authorized", {}).get("staker", {}) == MARINADE_STAKER_AUTHORITY
        ):
            return True

    return False


def handle_marinade_native_staking_create_tx(wallet_info, exporter, txinfo):
    wallet_info.set_marinade_native()
    row = _handle_generic(exporter, txinfo, TX_TYPE_SOL_STAKING_CREATE)
    row.comment += " [marinade_native]"
