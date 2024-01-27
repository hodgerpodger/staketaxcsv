import logging

import staketaxcsv.inj.constants as co
import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
from staketaxcsv.inj.config_inj import localconfig
from staketaxcsv.settings_csv import INJ_NODE
from staketaxcsv.inj import handle_deposit_claim, handle_send_to_eth


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_INJ, INJ_NODE)
    txinfo.url = "https://www.mintscan.io/injective/tx/{}".format(txinfo.txid)

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

        if msg_type == co.MSG_TYPE_DEPOSIT_CLAIM:
            handle_deposit_claim.handle_deposit_claim(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_SEND_TO_ETH:
            handle_send_to_eth.handle_send_to_eth(exporter, txinfo, msginfo)
        else:
            staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo
