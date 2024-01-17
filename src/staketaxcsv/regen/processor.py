import logging
import staketaxcsv.common.ibc.processor
import staketaxcsv.regen.constants as co
import staketaxcsv.common.ibc.processor
import staketaxcsv.common.ibc.handle
from staketaxcsv.regen.config_regen import localconfig
from staketaxcsv.settings_csv import REGEN_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(wallet_address, elem, co.MINTSCAN_LABEL_REGEN, REGEN_NODE)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
