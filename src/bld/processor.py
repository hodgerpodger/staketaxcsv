import logging
import common.ibc.processor
import bld.constants as co
import common.ibc.processor
import common.ibc.handle
from bld.config_bld import localconfig
from settings_csv import BLD_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_BLD, localconfig.ibc_addresses, BLD_NODE, co.EXCHANGE_BLD)

    for msginfo in txinfo.msgs:
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
