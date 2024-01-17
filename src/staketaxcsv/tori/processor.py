import logging

import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
import staketaxcsv.tori.constants as co
from staketaxcsv.settings_csv import TORI_NODE
from staketaxcsv.tori.config_tori import localconfig
from staketaxcsv.tori.handle import handle_airdrop


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_TORI, TORI_NODE)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        if msginfo.msg_type == 'MsgClaimAllocation':
            result_airdrop = handle_airdrop(exporter, txinfo, msginfo)
            if result_airdrop:
                continue

        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
