
import logging
import pprint
from datetime import datetime
from osmo.TxInfoOsmo import TxInfoOsmo, MsgInfo
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.handle_general import (
    handle_simple, handle_transfer_ibc,handle_failed_tx
)
from osmo.handle_staking import handle_staking
from osmo.handle_swap import handle_swap
from osmo import util_osmo
from osmo import constants as co


def process_txs(wallet_address, elems, exporter):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = _parse_tx(elem, wallet_address)

    # Detect failed transaction
    if elem["code"] > 0:
        handle_failed_tx(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        _handle_message(exporter, txinfo, msginfo)

    return txinfo


def _handle_message(exporter, txinfo, msginfo):
    try:
        msg_type = msginfo.message["@type"]

        if msg_type in [co.MSG_TYPE_VOTE]:
            handle_simple(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_DELEGATE, co.MSG_TYPE_REDELEGATE, co.MSG_TYPE_WITHDRAW_REWARD,
                          co.MSG_TYPE_WITHDRAW_COMMISSION, co.MSG_TYPE_UNDELEGATE]:
            handle_staking(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_IBC_TRANSFER, co.MSG_TYPE_MSGRECVPACKET]:
            handle_transfer_ibc(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_UPDATE_CLIENT:
            pass
        elif msg_type == co.MSG_TYPE_SWAP_IN:
            handle_swap(exporter, txinfo, msginfo)
        else:
            handle_unknown_detect_transfers(exporter, txinfo, msginfo)
    except Exception as e:
        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        handle_unknown_detect_transfers(exporter, txinfo, msginfo)

        # roger
        raise(e)

    return txinfo


def _parse_tx(elem, wallet_address):
    txid = elem["txhash"]
    timestamp = datetime.strptime(
        elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency = _fee(elem)

    # Construct list of MsgInfo's
    msgs = []
    for i in range(len(elem["logs"])):
        message = elem["tx"]["body"]["messages"][i]
        transfers = util_osmo._transfers(elem["logs"][i], wallet_address)
        row_txid = "{}-{}".format(txid, i)

        msginfo = MsgInfo(message, transfers, row_txid)
        msgs.append(msginfo)

    txinfo = TxInfoOsmo(txid, timestamp, fee, wallet_address, msgs)
    return txinfo


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
