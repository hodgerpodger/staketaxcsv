from staketaxcsv.common.ExporterTypes import (
    TX_TYPE_AIRDROP, TX_TYPE_NOOP, TX_TYPE_STAKING, TX_TYPE_UNKNOWN, TX_TYPE_SPEND, TX_TYPE_TRADE,
    TX_TYPE_SELF_TRANSFER)
from staketaxcsv.common import make_tx


def _make_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency, tx_type=None):
    if not tx_type:
        tx_type = "_" + msginfo.msg_type
    txid = "{}-{}".format(txinfo.txid, msginfo.msg_index)
    empty_fee = msginfo.msg_index > 0

    row = make_tx._make_tx_exchange(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, tx_type, txid=txid,
        empty_fee=empty_fee)

    _add_memo(row, txinfo)
    return row


def _add_memo(row, txinfo):
    # add memo to row comment (if memo exists)
    if txinfo.memo:
        if len(txinfo.memo) > 30:
            row.comment += "[memo:{}...]".format(txinfo.memo[:30])
        else:
            row.comment += "[memo:{}]".format(txinfo.memo)


def make_simple_tx_with_transfers(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)


def make_simple_tx(txinfo, msginfo, tx_type=None):
    return _make_tx(txinfo, msginfo, "", "", "", "", tx_type=tx_type)


def make_spend_tx_fee(txinfo, msginfo):
    row = _make_tx(txinfo, msginfo, txinfo.fee, txinfo.fee_currency, "", "", TX_TYPE_SPEND)
    row.fee = 0
    row.fee_currency = ""
    row.comment = msginfo.msg_type

    return row


def make_unknown_tx(txinfo, msginfo):
    return _make_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_UNKNOWN)


def make_unknown_tx_with_transfer(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx(
        txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency, tx_type=TX_TYPE_UNKNOWN)


def make_reward_tx(txinfo, msginfo, received_amount, received_currency):
    return _make_tx(txinfo, msginfo, "", "", received_amount, received_currency, TX_TYPE_STAKING)


def make_airdrop_tx(txinfo, msginfo, received_amount, received_currency):
    return _make_tx(txinfo, msginfo, "", "", received_amount, received_currency, TX_TYPE_AIRDROP)


def make_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_TRADE)


def make_transfer_in_tx(txinfo, msginfo, received_amount, received_currency):
    row = make_tx.make_transfer_in_tx(txinfo, received_amount, received_currency)
    row.txid = "{}-{}".format(txinfo.txid, msginfo.msg_index)
    _add_memo(row, txinfo)

    return row


def make_transfer_out_tx(txinfo, msginfo, sent_amount, sent_currency, dest=None):
    row = make_tx.make_transfer_out_tx(txinfo, sent_amount, sent_currency, dest)
    row.txid = "{}-{}".format(txinfo.txid, msginfo.msg_index)
    _add_memo(row, txinfo)

    return row


def make_self_transfer_tx(txinfo, msginfo):
    row = _make_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_SELF_TRANSFER)
    row.txid = "{}-{}".format(txinfo.txid, msginfo.msg_index)

    return row


def make_noop_tx(txinfo, msginfo):
    """ Known transaction that doesn't affect wallet account other than possible fee """
    return _make_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_NOOP)
