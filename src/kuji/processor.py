import logging

import common.ibc.processor
import common.ibc.handle
from kuji.config_kuji import localconfig
from common.cosmwasm.api_lcd_cosmwasm import CosmWasmLcdAPI, extract_msg
import kuji.constants as co
from settings_csv import KUJI_NODE

# Import contract handler functions
from kuji.contracts.config import CONTRACTS
import kuji.contracts.fin


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_KUJI, localconfig.ibc_addresses, KUJI_NODE)
    txinfo.url = "https://finder.kujira.app/kaiyo-1/tx/{}".format(txinfo.txid)

    if _is_execute_contract(txinfo):
        _handle_execute_contract(exporter, elem, txinfo)
    else:
        for msginfo in txinfo.msgs:
            result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
            if result:
                continue

            common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo


def _is_execute_contract(txinfo):
    return len(txinfo.msgs) > 0 and txinfo.msgs[0].msg_type == "MsgExecuteContract"


def _handle_execute_contract(exporter, elem, txinfo):
    contract = txinfo.msgs[0].contract

    # Find handler function for this contract
    if contract in CONTRACTS:
        # Found in luna2.contracts.*
        handler_func = CONTRACTS[contract]
    else:
        # Query contract metadata (to identify it)
        contract_history_data = _get_contract_history_data(contract)

        if kuji.contracts.fin.is_fin_contract(contract_history_data):
            handler_func = kuji.contracts.fin.handle_fin
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


def _get_contract_history_data(address):
    if address in localconfig.contract_history:
        return localconfig.contract_history[address]

    data = CosmWasmLcdAPI(KUJI_NODE).contract_history(address)
    msg = extract_msg(data)

    localconfig.contract_history[address] = msg
    return msg


def _handle_unknown(exporter, txinfo):
    row = common.make_tx.make_unknown_tx(txinfo)
    exporter.ingest_row(row)
