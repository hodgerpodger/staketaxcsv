import logging

import common.ibc.handle
import common.ibc.processor
import common.make_tx
from luna2.config_luna2 import localconfig
from luna2 import constants as co
from luna2.api_lcd import Luna2LcdAPI
from settings_csv import LUNA2_LCD_NODE

# Import contract handler functions
from luna2.contracts.config import CONTRACTS
import luna2.contracts.astroport
import luna2.contracts.treat_as_unknown
import luna2.contracts.valkyrie


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
    return len(txinfo.msgs) > 0 and txinfo.msgs[0].msg_type == "MsgExecuteContract"


def _handle_execute_contract(exporter, elem, txinfo):
    first_contract = txinfo.msgs[0].contract

    # Find handler function for this contract
    if first_contract in CONTRACTS:
        # Found in luna2.contracts.*
        handler_func = CONTRACTS[first_contract]
    else:
        # Query contract metadata (to identify it)
        contract_data = _get_contract_metadata(first_contract)

        if _is_astroport_pair_contract(contract_data):
            handler_func = luna2.contracts.astroport.handle_astroport
        else:
            # No handler found for this contract
            for msginfo in txinfo.msgs:
                common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
            return

    # Run handler function that returns CSV row(s)
    try:
        rows = handler_func(elem, txinfo)

        # Add row(s) to CSV
        common.make_tx.ingest_rows(exporter, txinfo, rows)
    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        _handle_unknown(exporter, txinfo)

        if localconfig.debug:
            raise e


def _get_contract_metadata(address):
    if address in localconfig.contracts:
        return localconfig.contracts[address]

    data = Luna2LcdAPI(LUNA2_LCD_NODE).contract(address)

    localconfig.contracts[address] = data
    return data


def _is_astroport_pair_contract(contract_data):
    return "contract_info" in contract_data and contract_data["contract_info"].get("label") == "Astroport pair"


def _handle_unknown(exporter, txinfo):
    row = common.make_tx.make_unknown_tx(txinfo)
    exporter.ingest_row(row)
