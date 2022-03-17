from terra import util_terra
from common.make_tx import make_spend_tx
from terra.col5.contracts.config import CONTRACTS
import terra.col5.contracts.astroport
import terra.col5.contracts.wormhole



def can_handle(exporter, elem, txinfo):
    # Has wasm event in every message
    for log in elem["logs"]:
        if "wasm" not in log["events_by_type"]:
            return False

    contract = util_terra._contract(elem, 0)
    return contract in CONTRACTS


def handle(exporter, elem, txinfo):
    rows = []

    # Lookup handler function from terra.col5.contracts.*
    contract = util_terra._contract(elem, 0)
    handler_func = CONTRACTS[contract]

    result_rows = handler_func(elem, txinfo)
    rows.extend(result_rows)

    _ingest_rows(exporter, txinfo, rows)


def _ingest_rows(exporter, txinfo, rows):
    # Add row(s) to CSV
    if len(rows) == 0:
        # No transactions.  Just make a "spend fee" row.
        if txinfo.fee:
            row = make_spend_tx(txinfo, txinfo.fee, txinfo.fee_currency)
            row.comment = "tx fee"
            rows.append(rows)
    else:
        for i, row in enumerate(rows):
            # Apply transaction fee to first row's fee column only
            if i == 0:
                row.fee = txinfo.fee
                row.fee_currency = txinfo.fee_currency
            else:
                row.fee = ""
                row.fee_currency = ""

            exporter.ingest_row(row)
