from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.common import make_tx

# These imports add to CONTRACTS dict
import staketaxcsv.luna1.col5.contracts.anchor
import staketaxcsv.luna1.col5.contracts.astroport
import staketaxcsv.luna1.col5.contracts.edge
import staketaxcsv.luna1.col5.contracts.mars
import staketaxcsv.luna1.col5.contracts.prism
import staketaxcsv.luna1.col5.contracts.pylon
import staketaxcsv.luna1.col5.contracts.wormhole
import staketaxcsv.luna1.col5.contracts.terraswap_route_swap
import staketaxcsv.luna1.col5.contracts.terranado


def can_handle(exporter, elem, txinfo):
    # Has wasm event in every message
    if "logs" in elem:
        for log in elem["logs"]:
            if "wasm" not in log["events_by_type"] and log["events_by_type"]["message"]["module"] != ["wasm"]:
                return False

    # TODO: REMOVE?
    # contract = util_terra._contract(elem, 0)
    return util_terra._any_contracts(CONTRACTS, elem)


def handle(exporter, elem, txinfo, index=0):
    # Lookup handler function from luna1.col5.contracts.*

    if len(txinfo.msgs) > 1:
        txinfo.comment += "Multiple msgs in tx. Count: {}".format(len(txinfo.msgs))

    try:
        contract = util_terra._contract(elem, index)
        handler_func = CONTRACTS[contract]
    except Exception as e:
        print("First contract not found in CONTRACTS dict. Trying next contract".format(txinfo.txid))
        handle(exporter, elem, txinfo, index + 1)
        return

    # Parse transaction data
    rows = handler_func(elem, txinfo)

    # Add row(s) to CSV
    make_tx.ingest_rows(exporter, txinfo, rows)
