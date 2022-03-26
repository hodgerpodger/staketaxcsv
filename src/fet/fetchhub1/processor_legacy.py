# For fetchhub-1 rpc data parsing

import logging
import base64
from fet.fetchhub1 import constants as co2
from fet.fetchhub1.api_rpc import RpcAPI
from fet.fetchhub1.TxInfoFet import TxInfoFet, MsgInfo
from fet.fetchhub1.handle_tx import handle_tx
import fet.handle_contract
import common.ibc.handle
from fet.config_fet import localconfig


def process_tx_legacy(wallet_address, elem, exporter, node):
    elem = _decode(elem)
    txinfo = _txinfo(wallet_address, elem, node)

    try:
        if txinfo.is_execute_contract():
            # Handle transaction with execute contract message(s)
            fet.handle_contract.handle_contract(exporter, txinfo)
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


def _decode(elem):
    """ Modifies transaction data with decoded version """
    elem["tx_result"]["log"] = eval(elem["tx_result"]["log"])
    elem["tx"] = _decode_tx(elem["tx"])

    events = elem["tx_result"]["events"]
    for event in events:
        for kv in event["attributes"]:
            k, v = kv["key"], kv["value"]

            kv["key"] = base64.b64decode(k).decode()
            kv["value"] = base64.b64decode(v).decode()

    return elem


def _decode_tx(tx):
    """ Naive way to decode tendermint tx without correct codec. """
    s = base64.b64decode(tx)
    return s


def _txinfo(wallet_address, elem, node):
    txid = elem["hash"]
    height = elem["height"]
    timestamp = RpcAPI(node).block_time(height)
    fee, fee_currency = _get_fee(elem)

    # Construct msgs: list of MsgInfoIBC objects
    msgs = []
    logs = elem["tx_result"]["log"]
    for i, log in enumerate(logs):
        message, msg_type = _message(log)
        transfers = _transfers(log, wallet_address)

        msginfo = MsgInfo(i, msg_type, message, transfers, log)
        msgs.append(msginfo)

    txinfo = TxInfoFet(txid, timestamp, fee, wallet_address, msgs)
    return txinfo


def _get_fee(elem):
    return "", ""


def _message(log):
    events = log["events"]
    for event in events:
        event_type = event["type"]
        attributes = event["attributes"]

        if event_type == "message":
            message = {}
            for kv in attributes:
                k, v = kv["key"], kv["value"]
                message[k] = v
            msg_type = message["action"]
            return message, msg_type

    return None, None


def _transfers(log, wallet_address):
    """ Returns (list of inbound transfers, list of outbound transfers), relative to wallet_address"""
    transfers_in, transfers_out = [], []

    events = log["events"]
    for event in events:
        event_type, attributes = event["type"], event["attributes"]

        if event_type == "transfer":
            # Handle all other cases
            for i in range(0, len(attributes), 3):
                recipient = attributes[i]["value"]
                sender = attributes[i + 1]["value"]
                amount_string = attributes[i + 2]["value"]

                if recipient == wallet_address:
                    for amount, currency in _amount_currency(amount_string):
                        transfers_in.append((amount, currency))
                elif sender == wallet_address:
                    for amount, currency in _amount_currency(amount_string):
                        transfers_out.append((amount, currency))
    return transfers_in, transfers_out


def _amount_currency(amount_string):
    # i.e. "13005419afet",
    out = []
    for amt_string in amount_string.split(","):
        if "u" in amt_string:
            uamount, ucurrency = amt_string.split("u", 1)
            currency = ucurrency.upper()
            amount = _amount(uamount, currency)
        elif "afet" in amt_string:
            uamount, ucurrency = amt_string.split("afet", 1)
            currency = co2.CUR_FET
            amount = _amount(uamount, currency)
        else:
            raise Exception("Unexpected amount_string: {}".format(amount_string))

        out.append((amount, currency))

    return out


def _amount(amount_string, currency):
    if currency == co2.CUR_FET:
        return float(amount_string) / co2.EXP18
    else:
        return float(amount_string) / co2.MILLION
