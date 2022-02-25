import logging
import common.ibc.processor
import huahua.constants as co
import common.ibc.processor
import common.ibc.handle
from huahua.config_huahua import localconfig
from settings_csv import HUAHUA_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.parse_txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_HUAHUA, co.EXCHANGE_HUAHUA, localconfig, HUAHUA_NODE)

    for msginfo in txinfo.msgs:
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if not result:
            common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
