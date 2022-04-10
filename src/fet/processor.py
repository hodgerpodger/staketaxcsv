import logging
import common.ibc.processor
import fet.constants as co
import fet.fetchhub1.constants as co2
import common.ibc.processor
import common.ibc.handle
import common.ibc.constants
from fet.config_fet import localconfig
from settings_csv import FET_NODE
from fet.fetchhub1.processor_legacy import process_tx_legacy
from fet.handle_tx import handle_tx
from fet.handle_contract import handle_contract


def process_txs(wallet_address, elems, exporter, node, progress=None):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter, node)

        # Update progress bar for slower processing of fetchhub-1 (due to required timestamp query for each tx)
        if node == co2.FET_FETCHUB1_NODE:
            if i % 10 == 0 or i == len(elems) - 1:
                message = f"Processed {i + 1} of {len(elems)} transactions for fetchhub1"
                progress.report(i + 1, message, progress.STAGE_FET1_TXS)


def process_tx(wallet_address, elem, exporter, node=None):
    if node and node in (co2.FET_FETCHUB1_NODE):
        return process_tx_legacy(wallet_address, elem, exporter, node)

    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_FET, co.EXCHANGE_FET, localconfig.ibc_addresses, FET_NODE)

    try:
        if txinfo.is_execute_contract():
            # Handle transaction with execute contract message(s)
            handle_contract(exporter, txinfo)
        else:
            # Handle all other transactions
            handle_tx(exporter, txinfo)
    except Exception as e:
        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        common.ibc.handle.handle_unknown_detect_transfers_tx(exporter, txinfo)
        if localconfig.debug:
            raise e

    return txinfo
