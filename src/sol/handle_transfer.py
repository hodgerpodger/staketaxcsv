from common.make_tx import make_transfer_in_tx, make_transfer_out_tx, make_transfer_self
from sol import util_sol
from sol.constants import (
    DIRECTION_INBOUND,
    DIRECTION_OUTBOUND,
    DIRECTION_SELF,
    INSTRUCT_TRANSFERCHECK,
    INSTRUCT_TRANSFERCHECKED,
    MINT_SOL,
)


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
    amount, currency, direction, dest_address = _get_transfer(txinfo)

    if direction == DIRECTION_OUTBOUND:
        row = make_transfer_out_tx(txinfo, amount, currency, dest_address)
        exporter.ingest_row(row)
    elif direction == DIRECTION_INBOUND:
        row = make_transfer_in_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    elif direction == DIRECTION_SELF:
        row = make_transfer_self(txinfo)
        exporter.ingest_row(row)
    else:
        raise Exception("Bad condition in handle_transfer()", txid, direction)


def _get_transfer(txinfo):
    txid = txinfo.txid
    instructions = txinfo.instructions
    wallet_address = txinfo.wallet_address
    account_to_mint = txinfo.account_to_mint

    for instruction in instructions:
        if "parsed" in instruction:
            parsed = instruction["parsed"]
            if parsed["type"] in ["transfer", "transferChecked"]:
                info = parsed["info"]

                amount_string = info.get("amount", None)
                lamports = info.get("lamports", None)
                token_amount = info.get("tokenAmount", None)
                authority = info.get("authority", None)
                source = info.get("source", None)
                destination = info.get("destination", None)

                if source is not None and source == destination:
                    # wallet transfering to self
                    return "", "", DIRECTION_SELF, destination
                if amount_string == "0":
                    continue

                # Determine mint and amount_string
                if amount_string:
                    mint = account_to_mint.get(source, None)
                elif lamports:
                    amount_string = lamports
                    mint = MINT_SOL
                elif token_amount:
                    amount_string = token_amount["amount"]
                    mint = account_to_mint.get(source, None)
                else:
                    raise Exception("Unable to find amount", txid)

                amount, currency = util_sol.amount_currency(txinfo, amount_string, mint)

                # Determine direction of transfer
                if authority == wallet_address:
                    direction = DIRECTION_OUTBOUND
                elif source == wallet_address:
                    direction = DIRECTION_OUTBOUND
                else:
                    direction = DIRECTION_INBOUND

                return amount, currency, direction, destination

    raise Exception("Unable to find transfer in _get_transfer()", txid)
