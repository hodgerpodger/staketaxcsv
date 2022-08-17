import logging

import common.ibc.handle
import common.ibc.processor
import common.make_tx
from luna2.config_luna2 import localconfig
from luna2 import constants as co
from settings_csv import LUNA2_LCD_NODE

# Import contract handler functions
from luna2.contracts.config import CONTRACTS
import luna2.contracts.astroport


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = _txinfo(wallet_address, elem)

    if _is_execute_contract(txinfo):
        _handle_execute_contract(exporter, elem, txinfo)
    else:
        for msginfo in txinfo.msgs:
            # Handle common ibc messages
            result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
            if result:
                continue

            # Handle unknown messages
            common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo


def _txinfo(wallet_address, elem):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, "dummy", localconfig.ibc_addresses, LUNA2_LCD_NODE, co.EXCHANGE_LUNA2)

    # Edit url, since terra not in mintscan
    txid = elem["txhash"]
    txinfo.url = "https://terrasco.pe/mainnet/tx/{}".format(txid)
    return txinfo


def _is_execute_contract(txinfo):
    if len(txinfo.msgs) > 0 and txinfo.msgs[0].msg_type == "MsgExecuteContract":
        return True
    else:
        return False


def _handle_execute_contract(exporter, elem, txinfo):
    first_contract = txinfo.msgs[0].contract

    if first_contract in CONTRACTS:
        try:
            # Lookup handler function from luna2.contracts.*
            handler_func = CONTRACTS[first_contract]

            # Run handler function that returns CSV row(s)
            rows = handler_func(elem, txinfo)

            # Add row(s) to CSV
            common.make_tx.ingest_rows(exporter, txinfo, rows)

        except Exception as e:
            logging.error("Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
            _handle_unknown(exporter, txinfo)

            if localconfig.debug:
                raise e

    else:
        logging.warning("Unknown contract: %s for txid=%s", first_contract, txinfo.txid)
        for msginfo in txinfo.msgs:
            common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def _handle_unknown(exporter, txinfo):
    row = common.make_tx.make_unknown_tx(txinfo)
    exporter.ingest_row(row)
