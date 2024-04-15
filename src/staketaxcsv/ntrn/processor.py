import logging

import staketaxcsv.ntrn.constants as co
import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
from staketaxcsv.ntrn.config_ntrn import localconfig
from staketaxcsv.settings_csv import NTRN_NODE
from staketaxcsv.common.ibc.api_lcd_cosmwasm import CosmWasmLcdAPI
import staketaxcsv.ntrn.astroport
import staketaxcsv.ntrn.vote


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_NTRN, NTRN_NODE)
    txinfo.url = "https://www.mintscan.io/neutron/tx/{}".format(txinfo.txid)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        if msginfo.msg_type == co.MSG_TYPE_EXECUTE_CONTRACT:
            _handle_execute_contract(exporter, txinfo, msginfo)
        else:
            staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo


def _handle_execute_contract(exporter, txinfo, msginfo):
    try:
        contract = msginfo.contract
        contract_data = _get_contract_data(contract)

        if staketaxcsv.ntrn.astroport.is_astroport_pair_contract(contract_data):
            staketaxcsv.ntrn.astroport.handle_astroport_swap(exporter, txinfo, msginfo)
            return
        if staketaxcsv.ntrn.vote.is_vote(contract_data):
            staketaxcsv.ntrn.vote.handle_vote(exporter, txinfo, msginfo)
            return
    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))

    staketaxcsv.common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def _get_contract_data(address):
    if address in localconfig.contracts:
        return localconfig.contracts[address]

    data = CosmWasmLcdAPI(NTRN_NODE).contract(address)

    localconfig.contracts[address] = data
    return data
