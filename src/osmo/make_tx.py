

from common.make_tx import (
    make_simple_tx, make_swap_tx, make_reward_tx, make_transfer_in_tx, make_transfer_out_tx,
    make_unknown_tx, make_unknown_tx_with_transfer
)


def make_osmo_simple_tx(txinfo, msginfo, tx_type):
    row = make_simple_tx(txinfo, tx_type)
    row.txid = msginfo.row_txid
    return row


def make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency):
    row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    row.txid = msginfo.row_txid
    return row


def make_osmo_reward_tx(txinfo, msginfo, reward_amount, reward_currency):
    row = make_reward_tx(txinfo, reward_amount, reward_currency)
    row.txid = msginfo.row_txid
    return row


def make_osmo_transfer_out_tx(txinfo, msginfo, sent_amount, sent_currency, dest_address=None):
    row = make_transfer_out_tx(txinfo, sent_amount, sent_currency, dest_address)
    row.txid = msginfo.row_txid
    return row


def make_osmo_transfer_in_tx(txinfo, msginfo, received_amount, received_currency):
    row = make_transfer_in_tx(txinfo, received_amount, received_currency)
    row.txid = msginfo.row_txid
    return row


def make_osmo_unknown_tx(txinfo, msginfo):
    row = make_unknown_tx(txinfo)
    row.txid = msginfo.row_txid
    return row


def make_osmo_unknown_tx_with_transfer(
        txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency, empty_fee=False, z_index=0):
    row = make_unknown_tx_with_transfer(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, empty_fee, z_index)
    row.txid = msginfo.row_txid
    return row
