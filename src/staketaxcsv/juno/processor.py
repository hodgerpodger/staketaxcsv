import logging

import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
import staketaxcsv.juno.constants as co
from staketaxcsv.juno.config_juno import localconfig
from staketaxcsv.settings_csv import JUNO_NODE
from staketaxcsv.common.make_tx import make_unknown_tx

CONTRACT_TRANSFER = ""


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_JUNO, JUNO_NODE)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    if _is_many_execute_contracts(txinfo):
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo


def _is_many_execute_contracts(txinfo):
    if len(txinfo.msgs) < 100:
        return False

    for msginfo in txinfo.msgs:
        if msginfo.msg_type != co.MSG_TYPE_EXECUTE_CONTRACT:
            return False
    return True
