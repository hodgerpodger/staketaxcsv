from common.Exporter import Row
from common.ExporterTypes import TX_TYPE_STAKING, TX_TYPE_UNKNOWN, TX_TYPE_NOOP
import common.make_tx
from common.ibc import util_ibc


def _make_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency, tx_type=None):
    if not tx_type:
        tx_type = "_" + msginfo.msg_type
    txid = "{}-{}".format(txinfo.txid, msginfo.msg_index)
    empty_fee = msginfo.msg_index > 0

    return common.make_tx._make_tx_exchange(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, tx_type, txid=txid,
        empty_fee=empty_fee)


def make_simple_tx_with_transfers(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)


def make_simple_tx(txinfo, msginfo):
    return _make_tx(txinfo, msginfo, "", "", "", "")


def make_unknown_tx(txinfo, msginfo):
    return _make_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_UNKNOWN)


def make_unknown_tx_with_transfer(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx(
        txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency, tx_type=TX_TYPE_UNKNOWN)


def make_reward_tx(txinfo, msginfo, received_amount, received_currency):
    return _make_tx(txinfo, msginfo, "", "", received_amount, received_currency, TX_TYPE_STAKING)


def make_transfer_in_tx(txinfo, msginfo, received_amount, received_currency):
    row = common.make_tx.make_transfer_in_tx(txinfo, received_amount, received_currency)
    row.txid = "{}-{}".format(txinfo.txid, msginfo.msg_index)
    return row


def make_transfer_out_tx(txinfo, msginfo, sent_amount, sent_currency, dest=None):
    row = common.make_tx.make_transfer_out_tx(txinfo, sent_amount, sent_currency, dest)
    row.txid = "{}-{}".format(txinfo.txid, msginfo.msg_index)
    return row


def make_noop_tx(txinfo, msginfo):
    """ Known transaction that doesn't affect wallet account other than possible fee """
    return _make_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_NOOP)
