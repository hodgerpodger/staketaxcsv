import staketaxcsv.inj
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.inj.config_inj import localconfig
from staketaxcsv.report_inj import _txdata
from staketaxcsv.settings_csv import TICKER_INJ
from tests.utils_ibc import apply_ibc_patches, load_tx


@apply_ibc_patches
def run_test_txids(wallet_address, txids):
    exporter = Exporter(wallet_address, localconfig, TICKER_INJ)
    txdata = _txdata()

    elems = []
    for txid in txids:
        elem = load_tx(wallet_address, txid, txdata.get_tx)
        elems.append(elem)

    staketaxcsv.inj.processor.process_txs(wallet_address, elems, exporter)
    return exporter.export_for_test()


def run_test(wallet_addres, txid):
    return run_test_txids(wallet_addres, [txid])
