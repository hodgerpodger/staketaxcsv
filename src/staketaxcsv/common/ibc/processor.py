"""
Special note on IBC receive: mintscan sometimes shows multiple transactions for same "IBC receive event":
  * I believe it's due to mintscan indexing on events: recv_packet.packet_data.receiver (or something similar)
  * Current solution: LCD queries for wallet only searches on events: message.sender and transfer.receipient .
                      This avoids multiple transactions for same "IBC receive event".
  * Found examples in JUNO.
"""

import logging
from datetime import datetime

import staketaxcsv.common.ibc.handle_authz
from staketaxcsv.common.ibc import constants as co
from staketaxcsv.common.ibc import handle, denoms
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.common.ibc.TxInfoIBC import TxInfoIBC
from staketaxcsv.common.make_tx import make_spend_fee_tx, make_simple_tx
from staketaxcsv.common.ExporterTypes import TX_TYPE_FAILED_NO_FEE
from staketaxcsv.common.ibc.handle_authz_no_logs import handle_authz_no_logs_tx, is_authz_no_logs_tx

MILLION = 1000000.0


def txinfo(wallet_address, elem, mintscan_label, lcd_node, customMsgInfo=None):
    """ Parses transaction data to return TxInfo object """
    txid = elem["txhash"]

    timestamp = datetime.strptime(elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency = _get_fee(wallet_address, elem, lcd_node)
    memo = _get_memo(elem)
    is_failed = ("code" in elem and elem["code"] > 0)

    if is_authz_no_logs_tx(elem):
        # special case for msgexec with logs element empty
        msgs = handle_authz_no_logs_tx(wallet_address, elem, lcd_node)
    else:
        # Construct msgs: list of MsgInfoIBC objects
        msgs = []
        if "logs" in elem and elem["logs"]:
            # Standard case using logs
            for i, log in enumerate(elem["logs"]):
                # Prevent crash in rare cases where msg_index field exists, with null value
                if "body" in elem["tx"] and "msg_index" in log and log["msg_index"] is None:
                    continue

                if "body" in elem["tx"]:
                    message = elem["tx"]["body"]["messages"][i]
                elif "value" in elem["tx"]:
                    message = elem["tx"]["value"]["msg"][i]
                else:
                    raise Exception("Unable to deduce message")

                if customMsgInfo:
                    msginfo = customMsgInfo(wallet_address, i, message, log, lcd_node)
                else:
                    msginfo = MsgInfoIBC(wallet_address, i, message, log, lcd_node)
                msgs.append(msginfo)

    txinfo = TxInfoIBC(txid, timestamp, fee, fee_currency, wallet_address, msgs, mintscan_label, memo, is_failed)
    return txinfo


def _get_fee(wallet_address, elem, lcd_node):
    if "auth_info" in elem["tx"]:
        amount_list = elem["tx"]["auth_info"]["fee"]["amount"]
    elif "value" in elem["tx"]:
        # legacy version (2021-ish)
        amount_list = elem["tx"]["value"]["fee"]["amount"]
    else:
        raise Exception("Unable to deduce fee")

    if len(amount_list) == 0:
        return "", ""

    # Get fee currency
    denom = amount_list[0]["denom"]

    # Get fee amount
    amount_string = amount_list[0]["amount"]

    fee, fee_currency = denoms.amount_currency_from_raw(amount_string, denom, lcd_node)

    if fee == 0:
        return "", ""
    else:
        return fee, fee_currency


def _get_memo(elem):
    tx = elem["tx"]
    if "body" in tx and "memo" in tx["body"]:
        return tx["body"]["memo"]
    else:
        return ""


def handle_message(exporter, txinfo, msginfo, debug=False):
    """ Parses message denoted by msginfo (for common ibc ecosystem types).  Returns True/False if handler found. """
    try:
        msg_type = msginfo.msg_type

        # Handle exec messages (wrapped messages; currently only for authz's restake)
        if msg_type == co.MSG_TYPE_EXEC:
            staketaxcsv.common.ibc.handle_authz.handle_exec(exporter, txinfo, msginfo)
            return True

        # authz
        elif msg_type == co.MSG_TYPE_GRANT:
            # grant message
            staketaxcsv.common.ibc.handle_authz.handle_authz_grant(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_REVOKE:
            # revoke message
            staketaxcsv.common.ibc.handle_authz.handle_authz_revoke(exporter, txinfo, msginfo)

        elif msg_type in [co.MSG_TYPE_VOTE, co.MSG_TYPE_SET_WITHDRAW_ADDRESS]:
            # simple transactions with no transfers
            handle.handle_simple(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_SUBMIT_PROPOSAL, co.MSG_TYPE_DEPOSIT]:
            transfers_in, transfers_out = msginfo.transfers

            if len(transfers_in) == 0 and len(transfers_out) == 1:
                # 1 outbound transfer
                handle.handle_simple_outbound(exporter, txinfo, msginfo)
            else:
                handle.handle_simple(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_UPDATE_CLIENT, co.MSG_TYPE_ACKNOWLEDGMENT]:
            pass

        # staking rewards
        elif msg_type in [co.MSG_TYPE_DELEGATE, co.MSG_TYPE_DELEGATE_TO_VALIDATOR_SET,
                          co.MSG_TYPE_REDELEGATE, co.MSG_TYPE_WITHDRAW_DELEGATION_REWARDS,
                          co.MSG_TYPE_WITHDRAW_REWARD, co.MSG_TYPE_WITHDRAW_COMMISSION,
                          co.MSG_TYPE_UNDELEGATE, co.MSG_TYPE_UNDELEGATE_FROM_REBALANCED_VALIDATOR_SET,
                          co.MSG_TYPE_UNDELEGATE_FROM_VALIDATOR_SET]:
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
            raise e

        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        handle.handle_unknown(exporter, txinfo, msginfo)
        return True


def handle_failed_transaction(exporter, txinfo):
    """ Treat failed transaction as spend fee transaction (unless fee is 0). """
    if txinfo.fee:
        # Make a spend fee csv row
        row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        row.comment = "fee for failed transaction"
        row.fee = ""
        row.fee_currency = ""
        exporter.ingest_row(row)
    else:
        # No fee
        row = make_simple_tx(txinfo, TX_TYPE_FAILED_NO_FEE)
        row.comment = "failed transaction"
        exporter.ingest_row(row)
