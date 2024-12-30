from staketaxcsv.common.ExporterTypes import TX_TYPE_SOL_CLOSE_ACCOUNT, TX_TYPE_SOL_INIT_ACCOUNT
from staketaxcsv.sol.constants import (
    INSTRUCTION_TYPE_CLOSE_ACCOUNT,
    INSTRUCTION_TYPE_CREATE_ACCOUNT,
    INSTRUCTION_TYPE_INITIALIZE,
    INSTRUCTION_TYPE_INITIALIZE_ACCOUNT,
    PROGRAM_SPL_ASSOCIATED_TOKEN_ACCOUNT,
    PROGRAM_SPL_TOKEN,
    CURRENCY_SOL,
)
from staketaxcsv.sol.handle_simple import _handle_generic
from staketaxcsv.sol.util_sol import is_staking_account
from staketaxcsv.common.make_tx import make_reward_tx


INSTRUCTION_TYPES_INIT = set([
    INSTRUCTION_TYPE_CREATE_ACCOUNT,
    INSTRUCTION_TYPE_INITIALIZE,
    INSTRUCTION_TYPE_INITIALIZE_ACCOUNT
])


def is_init_account_tx(txinfo):
    instructions = txinfo.instructions
    instruction_types = txinfo.instruction_types
    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if (len(instructions) == 1
       and instructions[0].get("program", None) == PROGRAM_SPL_ASSOCIATED_TOKEN_ACCOUNT):
        return True

    if len(transfers_in) > 0 or len(transfers_out) > 0 or len(transfers_unknown) > 0:
        return False

    if len(instruction_types) == 0:
        return False

    for instruction_type, program in instruction_types:
        if instruction_type not in INSTRUCTION_TYPES_INIT:
            return False

    return True


def handle_init_account_tx(exporter, txinfo):
    _handle_generic(exporter, txinfo, TX_TYPE_SOL_INIT_ACCOUNT)


def is_close_account_tx(txinfo):
    instruction_types = txinfo.instruction_types

    if (len(instruction_types) == 1
       and instruction_types[0][0] == INSTRUCTION_TYPE_CLOSE_ACCOUNT
       and instruction_types[0][1] == PROGRAM_SPL_TOKEN):
        return True
    else:
        return False


def handle_close_account_tx(exporter, txinfo):
    _handle_generic(exporter, txinfo, TX_TYPE_SOL_CLOSE_ACCOUNT)


def handle_claim_staking_tip(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net
    log_instructions = txinfo.log_instructions
    wallet_address = txinfo.wallet_address

    if (
        len(transfers_in) == 1
        and "Claim" in log_instructions
        and is_staking_account(wallet_address)
    ):
        rec_amount, rec_currency, _, _ = transfers_in[0]
        if rec_currency == CURRENCY_SOL:
            row = make_reward_tx(txinfo, rec_amount, rec_currency)
            row.comment = "claim tx for {}".format(wallet_address)
            exporter.ingest_row(row)
            return

    raise Exception("Unable to handle tx in handle_claim_staking_tip()")
