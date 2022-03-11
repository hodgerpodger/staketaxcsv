"""
Special note on IBC receive: mintscan sometimes shows multiple transactions for same "IBC receive event":
  * I believe it's due to mintscan indexing on events: recv_packet.packet_data.receiver (or something similar)
  * Current solution: LCD queries for wallet only searches on events: message.sender and transfer.receipient .
                      This avoids multiple transactions for same "IBC receive event".
  * Found examples in JUNO.
"""

import logging
from datetime import datetime
from common.ibc import constants as co
from common.ibc import util_ibc
from common.ibc.TxInfoIBC import TxInfoIBC
from common.ibc.MsgInfoIBC import MsgInfoIBC
from common.ibc import handle

MILLION = 1000000.0


def txinfo(wallet_address, elem, mintscan_label, exchange, ibc_addresses, lcd_node):
    """ Parses transaction data to return TxInfo object """
    txid = elem["txhash"]
    timestamp = datetime.strptime(elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency = _get_fee(elem)

    # Parse elem data into list of MsgInfoIBC objects
    msgs = []
    for i in range(len(elem["logs"])):
        message = elem["tx"]["body"]["messages"][i]
        log = elem["logs"][i]

        msginfo = MsgInfoIBC(wallet_address, i, message, log, lcd_node, ibc_addresses)
        msgs.append(msginfo)

    txinfo = TxInfoIBC(txid, timestamp, fee, fee_currency, wallet_address, msgs, mintscan_label, exchange)
    return txinfo


def _get_fee(elem):
    amount_list = elem["tx"]["auth_info"]["fee"]["amount"]
    if len(amount_list) == 0:
        return 0, ""

    # Get fee amount
    amount_string = amount_list[0]["amount"]
    fee = float(amount_string) / MILLION
    if fee == 0:
        return 0, ""

    # Get fee currency
    denom = amount_list[0]["denom"]
    if denom.startswith("u"):
        fee_currency = denom[1:].upper()
    else:
        raise Exception("Unexpected denom={}".format(denom))

    return fee, fee_currency


def handle_message(exporter, txinfo, msginfo, debug=False):
    """ Parses message denoted by msginfo (for common ibc ecosystem types).  Returns True/False if handler found. """
    try:
        msg_type = msginfo.msg_type

        # simple transactions, that are typically ignored
        if msg_type in [co.MSG_TYPE_VOTE, co.MSG_TYPE_SET_WITHDRAW_ADDRESS]:
            # 0 transfers
            handle.handle_simple(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_SUBMIT_PROPOSAL, co.MSG_TYPE_DEPOSIT]:
            # 1 outbound transfer
            handle.handle_simple_outbound(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_UPDATE_CLIENT, co.MSG_TYPE_ACKNOWLEDGMENT]:
            pass

        # staking rewards
        elif msg_type in [co.MSG_TYPE_DELEGATE, co.MSG_TYPE_REDELEGATE, co.MSG_TYPE_WITHDRAW_REWARD,
                          co.MSG_TYPE_WITHDRAW_COMMISSION, co.MSG_TYPE_UNDELEGATE]:
            handle.handle_staking(exporter, txinfo, msginfo)

        # transfers
        elif msg_type == co.MSG_TYPE_SEND:
            handle.handle_transfer(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_MULTI_SEND:
            handle.handle_multisend(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_IBC_TRANSFER, co.MSG_TYPE_MSGRECVPACKET]:
            handle.handle_transfer_ibc(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_TIMEOUT:
            # ibc transfer timeout
            pass

        else:
            return False

        return True

    except Exception as e:
        if debug:
            raise(e)

        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        handle.handle_unknown(exporter, txinfo, msginfo)
        return True
