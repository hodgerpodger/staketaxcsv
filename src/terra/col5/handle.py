import common.make_tx
from terra import util_terra
from terra.col5.contracts.config import CONTRACTS
import terra.col5.contracts.astroport
import terra.col5.contracts.wormhole
import terra.col5.contracts.terraswap_route_swap


def can_handle(exporter, elem, txinfo):
    # Has wasm event in every message
    for log in elem["logs"]:
        if "wasm" not in log["events_by_type"]:
            return False

    contract = util_terra._contract(elem, 0)
    return contract in CONTRACTS


def handle(exporter, elem, txinfo):
    # Lookup handler function from terra.col5.contracts.*
    contract = util_terra._contract(elem, 0)
    handler_func = CONTRACTS[contract]

    # Parse transaction data
    rows = handler_func(elem, txinfo)

    # Add row(s) to CSV
    common.make_tx.ingest_rows(exporter, txinfo, rows)
