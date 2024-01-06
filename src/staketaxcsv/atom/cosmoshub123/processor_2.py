"""
Transactions processor for cosmoshub2 transactions.
"""


import logging

from staketaxcsv.atom.config_atom import localconfig
from staketaxcsv.atom.constants import CHAIN_ID_COSMOSHUB2, CUR_ATOM, MILLION
from staketaxcsv.atom.cosmoshub123.make_tx import make_atom_reward_tx, make_transfer_receive_tx
from staketaxcsv.atom.TxInfoAtom import TxInfoAtom
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.ExporterTypes import (
    TX_TYPE_UNKNOWN,
    TX_TYPE_VOTE,
)
from staketaxcsv.common.make_tx import make_simple_tx, make_transfer_out_tx, make_spend_fee_tx


def _parse_timestamp(timestamp):
    # 2019-12-04T18:12:09Z or '2019-12-04T18:12:09.0123345678Z'
    return timestamp.split('.')[0].replace("Z", "").replace("T", " ")


def process_tx(wallet_address, elem, exporter):
    txid = elem["txhash"]

    chain_id = CHAIN_ID_COSMOSHUB2
    timestamp = _parse_timestamp(elem["timestamp"])
    fee = _get_fee(elem)
    url = "https://www.mintscan.io/cosmos/txs/{}".format(txid)

    msg_types = _msg_types(elem)
    for i in range(0, len(msg_types)):
        msg_type = msg_types[i]

        # Make new unique TxInfoAtom for each message
        cur_txid = "{}-{}".format(txid, i)
        cur_fee = fee if i == 0 else ""
        txinfo = TxInfoAtom(cur_txid, timestamp, cur_fee, wallet_address, url, chain_id)

        try:
            _handle_tx(msg_type, exporter, txinfo, elem, txid, i)
        except Exception as e:
            logging.error("Exception when handling txid=%s, exception:%s", txid, str(e))
            handle_simple_tx(exporter, txinfo, TX_TYPE_UNKNOWN)

            if localconfig.debug:
                raise e


def _handle_tx(msg_type, exporter, txinfo, elem, txid, i):
    if not elem["logs"][0]["success"]:
        logging.info("Detected failed transaction")

        row = make_spend_fee_tx(txinfo, txinfo.fee, CUR_ATOM)
        row.comment = "Fee for failed transaction"
        exporter.ingest_row(row)
        return

    if msg_type in ("MsgSend", "MsgCreateVestingAccount"):
        handle_transfer(exporter, txinfo, elem, i)
    elif msg_type in ("MsgWithdrawDelegatorReward", "MsgWithdrawDelegationReward"):
        handle_withdraw_reward(exporter, txinfo, elem, i)
    elif msg_type in ["MsgDelegate", "MsgUndelegate", "MsgBeginRedelegate"]:
        handle_del_reward(exporter, txinfo, elem, i, msg_type)
    elif msg_type == "MsgVote":
        handle_simple_tx(exporter, txinfo, TX_TYPE_VOTE)
    elif msg_type == "MsgUpdateClient":
        # IBC Update Client message: skip (comes with additional messages of interest)
        return
    else:
        logging.error("Unknown msg_type=%s", msg_type)
        ErrorCounter.increment("unknown_msg_type_" + msg_type, txid)
        handle_simple_tx(exporter, txinfo, TX_TYPE_UNKNOWN)


def handle_simple_tx(exporter, txinfo, tx_type):
    row = make_simple_tx(txinfo, tx_type)
    exporter.ingest_row(row)


def handle_unknown(exporter, txinfo):
    return handle_simple_tx(exporter, txinfo, TX_TYPE_UNKNOWN)


def handle_del_reward(exporter, txinfo, elem, msg_index, msg_type):
    raise Exception("claimed reward amount in this older transaction data format unavailable for delegate/redelegate")


def handle_transfer(exporter, txinfo, elem, msg_index):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    msg_value = elem["tx"]["value"]["msg"][0]["value"]

    from_address = msg_value["from_address"]
    to_address = msg_value["to_address"]
    amount_string = msg_value["amount"][0]["amount"] + msg_value["amount"][0]["denom"]
    amount, currency = _amount(amount_string)

    if wallet_address == from_address:
        row = make_transfer_out_tx(txinfo, amount, currency, to_address)
        exporter.ingest_row(row)
    elif wallet_address == to_address:
        row = make_transfer_receive_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    else:
        raise Exception("unable to handle transfer in processor_12.py")


def handle_withdraw_reward(exporter, txinfo, elem, msg_index):
    amount_string = elem["tags"][1]["value"]
    assert (elem["tags"][1]["key"] == "rewards")

    amount, currency = _amount(amount_string)

    if amount:
        row = make_atom_reward_tx(txinfo, amount)
        exporter.ingest_row(row)


def _atom(uatom):
    """
    Example: '5340003uatom' -> 5.340003
    """
    amount, currency = _amount(uatom)
    assert currency == CUR_ATOM
    return amount


def _amount(amount_string):
    # Example: '5340003uatom' -> 5.340003
    if amount_string == "":
        return 0, None

    amount, currency = amount_string.split("u", 1)
    amount = float(amount) / MILLION
    currency = currency.upper()

    return amount, currency


def _get_fee(elem):
    # legacy cosmohub123 format
    amount_list = elem["tx"]["value"]["fee"]["amount"]
    if not amount_list:
        return 0

    amount_string = amount_list[0]["amount"]
    fee = float(amount_string) / MILLION
    return fee


def _msg_types(elem):
    # legacy cosmoshub123 format (i.e. cosmos-sdk/MsgWithdrawDelegationReward -> MsgWithdrawDelegationReward)
    types = [msg["type"] for msg in elem["tx"]["value"]["msg"]]

    out = []
    for t in types:
        lastfield = t.split("/")[-1]
        out.append(lastfield)
    return out
