import logging

import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
import staketaxcsv.common.make_tx
import staketaxcsv.luna2.contracts.astroport
import staketaxcsv.luna2.contracts.general
import staketaxcsv.luna2.contracts.valkyrie
from staketaxcsv.common.ibc.api_lcd_cosmwasm import CosmWasmLcdAPI
from staketaxcsv.luna2 import constants as co
from staketaxcsv.luna2.config_luna2 import localconfig

# Import contract handler functions
from staketaxcsv.luna2.contracts.config import CONTRACTS
from staketaxcsv.settings_csv import LUNA2_LCD_NODE

CONTRACT_VKR_TOKEN = "terra1gy73st560m2j0esw5c5rjmr899hvtv4rhh4seeajt3clfhr4aupszjss4j"
CONTRACTS_USE_SECOND_MESSAGE = set([
    CONTRACT_VKR_TOKEN
])


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
            result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
            if result:
                continue

            # Handle unknown messages
            staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo


def _txinfo(wallet_address, elem):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, "dummy", localconfig.ibc_addresses, LUNA2_LCD_NODE)

    # Edit url, since terra not in mintscan
    txid = elem["txhash"]
    txinfo.url = "https://terrasco.pe/mainnet/tx/{}".format(txid)
    return txinfo


def _is_execute_contract(txinfo):
    return len(txinfo.msgs) > 0 and txinfo.msgs[0].msg_type == "MsgExecuteContract"


def _handle_execute_contract(exporter, elem, txinfo):
    contract = txinfo.msgs[0].contract
    if contract in CONTRACTS_USE_SECOND_MESSAGE and len(txinfo.msgs) > 1:
        contract = txinfo.msgs[1].contract

    # Find handler function for this contract
    if contract in CONTRACTS:
        # Found in luna2.contracts.*
        handler_func = CONTRACTS[contract]
    else:
        # Query contract data (to identify it)
        contract_data = _get_contract_data(contract)

        if staketaxcsv.luna2.contracts.astroport.is_astroport_pair_contract(contract_data):
            handler_func = staketaxcsv.luna2.contracts.astroport.handle_astroport
        else:
            # No handler found for this contract
            for msginfo in txinfo.msgs:
                staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
            return

    # Run handler function that returns CSV row(s)
    try:
        rows = handler_func(elem, txinfo)

        # Add row(s) to CSV
        staketaxcsv.common.make_tx.ingest_rows(exporter, txinfo, rows)
    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        _handle_unknown(exporter, txinfo)

        if localconfig.debug:
            raise e


def _get_contract_data(address):
    if address in localconfig.contracts:
        return localconfig.contracts[address]

    data = CosmWasmLcdAPI(LUNA2_LCD_NODE).contract(address)

    localconfig.contracts[address] = data
    return data



def _handle_unknown(exporter, txinfo):
    row = staketaxcsv.common.make_tx.make_unknown_tx(txinfo)
    exporter.ingest_row(row)
