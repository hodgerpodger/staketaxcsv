import logging

import staketaxcsv.strd.constants as co
import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
from staketaxcsv.strd.config_strd import localconfig
from staketaxcsv.settings_csv import STRD_NODE
from staketaxcsv.strd import handle


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_STRD, STRD_NODE)
    txinfo.url = "https://www.mintscan.io/stride/tx/{}".format(txinfo.txid)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        _handle_message(exporter, txinfo, msginfo)

    return txinfo


def _handle_message(exporter, txinfo, msginfo):
    try:
        msg_type = msginfo.msg_type

        if msg_type == co.MSG_TYPE_CLAIM_FREE_AMOUNT:
            handle.handle_claim_free_amount(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LIQUID_STAKE:
            handle.handle_liquid_stake(exporter, txinfo, msginfo)
        else:
            staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
