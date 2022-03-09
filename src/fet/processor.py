import logging
import common.ibc.processor
import fet.constants as co
import common.ibc.processor
import common.ibc.handle
from fet.config_fet import localconfig
from settings_csv import FET_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_FET, co.EXCHANGE_FET, localconfig.ibc_addresses, FET_NODE)

    for msginfo in txinfo.msgs:
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
