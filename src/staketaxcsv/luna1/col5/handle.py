import staketaxcsv.common.make_tx
import staketaxcsv.luna1.col5.contracts.astroport
import staketaxcsv.luna1.col5.contracts.terraswap_route_swap
import staketaxcsv.luna1.col5.contracts.wormhole
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS


def can_handle(exporter, elem, txinfo):
    # Has wasm event in every message
    for log in elem["logs"]:
        if "wasm" not in log["events_by_type"]:
            return False

    contract = util_terra._contract(elem, 0)
    return contract in CONTRACTS


def handle(exporter, elem, txinfo):
    # Lookup handler function from luna1.col5.contracts.*
    contract = util_terra._contract(elem, 0)
    handler_func = CONTRACTS[contract]

    # Parse transaction data
    rows = handler_func(elem, txinfo)

    # Add row(s) to CSV
    common.make_tx.ingest_rows(exporter, txinfo, rows)
