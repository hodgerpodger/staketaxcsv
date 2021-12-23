
from common.Exporter import (
    TX_TYPE_LP_DEPOSIT, TX_TYPE_LP_WITHDRAW, TX_TYPE_LP_STAKE, TX_TYPE_LP_UNSTAKE
)
from common.make_tx import (
    make_simple_tx, make_swap_tx, make_reward_tx, make_transfer_in_tx, make_transfer_out_tx,
    make_unknown_tx, make_unknown_tx_with_transfer, _make_tx_exchange, _make_tx_sent, _make_tx_received
)
from osmo import util_osmo


def _edit_row(row, txinfo, msginfo):
    row.txid = txinfo.txid + "-" + str(msginfo.msg_index)
    if msginfo.msg_index > 0:
        row.fee = ""
        row.fee_currency = ""


def make_osmo_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency,
                 txid=None, empty_fee=False):
    tx_type = util_osmo._make_tx_type(msginfo)
    row = _make_tx_exchange(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, tx_type,
        txid=txid, empty_fee=empty_fee)
    _edit_row(row, txinfo, msginfo)
    return row


def make_osmo_simple_tx(txinfo, msginfo):
    row = make_osmo_tx(txinfo, msginfo, "", "", "", "")
    return row


def make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency):
    row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    _edit_row(row, txinfo, msginfo)
    return row


def make_osmo_reward_tx(txinfo, msginfo, reward_amount, reward_currency):
    row = make_reward_tx(txinfo, reward_amount, reward_currency)
    _edit_row(row, txinfo, msginfo)
    return row


def make_osmo_transfer_out_tx(txinfo, msginfo, sent_amount, sent_currency, dest_address=None):
    row = make_transfer_out_tx(txinfo, sent_amount, sent_currency, dest_address)
    _edit_row(row, txinfo, msginfo)
    return row


def make_osmo_transfer_in_tx(txinfo, msginfo, received_amount, received_currency):
    row = make_transfer_in_tx(txinfo, received_amount, received_currency)
    _edit_row(row, txinfo, msginfo)
    return row


def make_osmo_unknown_tx(txinfo, msginfo):
    row = make_unknown_tx(txinfo)
    _edit_row(row, txinfo, msginfo)
    return row


def make_osmo_unknown_tx_with_transfer(txinfo, msginfo, sent_amount, sent_currency, received_amount,
                                       received_currency, empty_fee=False, z_index=0):
    row = make_unknown_tx_with_transfer(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, empty_fee, z_index)
    _edit_row(row, txinfo, msginfo)
    return row


def make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount, sent_currency, lp_amount, lp_currency, empty_fee=False):
    row = make_osmo_tx(txinfo, msginfo, sent_amount, sent_currency, lp_amount, lp_currency,
                       txid=None, empty_fee=empty_fee)
    return row


def make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount, lp_currency, received_amount, received_currency,
                             empty_fee=False):
    row = make_osmo_tx(txinfo, msginfo, lp_amount, lp_currency, received_amount, received_currency,
                       txid=None, empty_fee=empty_fee)
    return row


def make_osmo_lp_stake_tx(txinfo, msginfo, lp_amount, lp_currency):
    row = make_osmo_tx(txinfo, msginfo, lp_amount, lp_currency, "", "")
    return row


def make_osmo_lp_unstake_tx(txinfo, msginfo, lp_amount, lp_currency):
    row = make_osmo_tx(txinfo, msginfo, "", "", lp_amount, lp_currency)
    return row
