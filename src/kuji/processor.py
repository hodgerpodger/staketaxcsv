import logging
import common.ibc.processor
import kuji.constants as co
import common.ibc.processor
import common.ibc.handle
from kuji.config_kuji import localconfig
from settings_csv import KUJI_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_KUJI, localconfig.ibc_addresses, KUJI_NODE)
    txinfo.url = "https://finder.kujira.app/kaiyo-1/tx/{}".format(txinfo.txid)

    for msginfo in txinfo.msgs:
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
