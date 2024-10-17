import logging

import staketaxcsv.report_osmo
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.settings_csv import TICKER_OSMO
from staketaxcsv.common.Exporter import Exporter
import staketaxcsv.osmo.api_data
import staketaxcsv.osmo.processor
from staketaxcsv.report_osmo import _txdata
from tests.utils_ibc import apply_ibc_patches, load_tx
RETURN_TYPE_EXPORTER = "exporter"


def run_test(wallet_address, txid):
    return run_test_txids(wallet_address, [txid])


def run_test_verbose(wallet_address, txid):
    return run_test_txids(wallet_address, [txid], truncate=False)


@apply_ibc_patches
def run_test_txids(wallet_address, txids, truncate=True):
    exporter = Exporter(wallet_address, localconfig, TICKER_OSMO)
    txdata = _txdata()

    elems = []
    for txid in txids:
        elem = load_tx(wallet_address, txid, txdata.get_tx)
        elems.append(elem)

    staketaxcsv.osmo.processor.process_txs(wallet_address, elems, exporter)

    if truncate:
        return exporter.export_for_test()
    else:
        return exporter.export_string()
