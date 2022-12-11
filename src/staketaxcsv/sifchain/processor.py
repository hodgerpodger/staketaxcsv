import logging

import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
import staketaxcsv.sifchain.constants as co
from staketaxcsv.settings_csv import SIFCHAIN_NODE
from staketaxcsv.sifchain.config_sifchain import localconfig


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_SIFCHAIN, localconfig.ibc_addresses, SIFCHAIN_NODE)

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
