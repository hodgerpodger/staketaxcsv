import logging

import staketaxcsv.tia.constants as co
import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
from staketaxcsv.tia.config_tia import localconfig
from staketaxcsv.settings_csv import TIA_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_TIA, TIA_NODE)
    txinfo.url = "https://www.mintscan.io/celestia/tx/{}".format(txinfo.txid)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
