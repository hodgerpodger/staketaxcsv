import logging
import common.ibc.processor
import stargaze.constants as co
import common.ibc.processor
import common.ibc.handle
from stargaze.config_stargaze import localconfig
from settings_csv import STARGAZE_NODE
from stargaze.handle import handle_airdrop


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_STARGAZE, co.EXCHANGE_STARGAZE, localconfig.ibc_addresses, STARGAZE_NODE)

    for msginfo in txinfo.msgs:
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        if msginfo.msg_type == 'MsgInitialClaim':
            result_airdrop = handle_airdrop(exporter, txinfo, msginfo)
            if result_airdrop:
                continue

        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
