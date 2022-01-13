from common.make_tx import make_transfer_in_tx
from sol.constants import BILLION, CURRENCY_SOL
from sol.handle_simple import handle_unknown_detect_transfers


def handle_vote(exporter, txinfo):
    instruction_types = txinfo.instruction_types
    instructions = txinfo.instructions
    wallet_accounts = txinfo.wallet_accounts

    if len(instruction_types) == 1 and instruction_types[0][0] == "withdraw":
        info = instructions[0]["parsed"]["info"]
        destination = info["destination"]
        lamports = info["lamports"]
        if destination in wallet_accounts:
            amount = float(lamports) / BILLION
            row = make_transfer_in_tx(txinfo, amount, CURRENCY_SOL)

            # Override explorer url because solscan unable to locate this type of transaction
            row.url = "https://explorer.solana.com/tx/{}".format(txinfo.txid)

            exporter.ingest_row(row)
            return

    handle_unknown_detect_transfers(exporter, txinfo)
