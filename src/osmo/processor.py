
import logging
import pprint
from datetime import datetime
from osmo.TxInfoOsmo import TxInfoOsmo
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.handle_general import (
    handle_delegate, handle_withdraw_reward, handle_simple, handle_transfer_ibc,
    handle_failed_tx
)
from osmo.handle_swap import handle_swap
from osmo import util_osmo
from osmo import constants as co


def process_txs(wallet_address, elems, exporter):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = _parse_tx(elem, wallet_address)
    msgs = txinfo.msgs

    # Detect failed transaction
    if elem["code"] > 0:
        handle_failed_tx(exporter, txinfo)
        return txinfo

    for message, transfers in msgs:
        # Process message
        try:
            msg_type = message["@type"]

            if msg_type in [co.MSG_TYPE_VOTE]:
                handle_simple(exporter, txinfo, message, transfers)
            elif msg_type == co.MSG_TYPE_DELEGATE:
                handle_delegate(exporter, txinfo, message, transfers)
            elif msg_type == co.MSG_TYPE_WITHDRAW_REWARD:
                handle_withdraw_reward(exporter, txinfo, message, transfers)
            elif msg_type == co.MSG_TYPE_IBC_TRANSFER:
                handle_transfer_ibc(exporter, txinfo, message, transfers)
            elif msg_type == co.MSG_TYPE_MSGRECVPACKET:
                handle_transfer_ibc(exporter, txinfo, message, transfers)
            elif msg_type == co.MSG_TYPE_UPDATE_CLIENT:
                continue
            elif msg_type == co.MSG_TYPE_SWAP_IN:
                handle_swap(exporter, txinfo, message, transfers)
            else:
                handle_unknown_detect_transfers(exporter, txinfo, transfers)
        except Exception as e:
            logging.error(
                "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
            handle_unknown_detect_transfers(exporter, txinfo, transfers)

    return txinfo


def _parse_tx(elem, wallet_address):
    txid = elem["txhash"]
    timestamp = datetime.strptime(
        elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency = _fee(elem)

    txinfo = TxInfoOsmo(txid, timestamp, fee, wallet_address)
    txinfo.msgs = _msgs(elem, wallet_address)
    return txinfo


def _msgs(elem, wallet_address):
    out = []

    num_messages = len(elem["logs"])
    for i in range(num_messages):
        message = elem["tx"]["body"]["messages"][i]
        log = elem["logs"][i]
        transfers = util_osmo._transfers(log, wallet_address)

        out.append((message, transfers))
    return out


def _fee(elem):
    fees = elem["tx"]["auth_info"]["fee"]["amount"]
    if len(fees) == 0:
        return "", ""

    first_fee = fees[0]
    fee_amount = float(first_fee["amount"]) / co.MILLION
    fee_currency = co.CUR_OSMO

    if not fee_amount:
        return "", ""
    return fee_amount, fee_currency
