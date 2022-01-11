from common.Exporter import Row
from common.ExporterTypes import TX_TYPE_STAKING
from common.make_tx import (
    _make_tx_exchange,
    make_reward_tx,
    make_swap_tx,
    make_transfer_in_tx,
    make_transfer_out_tx,
    make_unknown_tx,
    make_unknown_tx_with_transfer,
)
from osmo import util_osmo
from osmo.constants import EXCHANGE_OSMOSIS


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


def make_lp_reward_tx(wallet_address, day, reward_amount, reward_currency):
    timestamp = "{} 17:00:00".format(day)
    txid = "{}.{}.{}".format(wallet_address, day, reward_currency)
    row = Row(
        timestamp=timestamp,
        tx_type=TX_TYPE_STAKING,
        received_amount=reward_amount,
        received_currency=reward_currency,
        sent_amount="",
        sent_currency="",
        fee="",
        fee_currency="",
        exchange=EXCHANGE_OSMOSIS,
        wallet_address=wallet_address,
        txid=txid,
        url=""
    )
    row.comment = "lp_reward"
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


def make_osmo_lp_stake_tx(txinfo, msginfo, lp_amount, lp_currency, period_lock_id):
    row = make_osmo_tx(txinfo, msginfo, lp_amount, lp_currency, "", "")
    row.comment = "lp stake (period_lock_id: {})".format(period_lock_id)
    return row


def make_osmo_lp_unstake_tx(txinfo, msginfo, lp_amount, lp_currency, period_lock_id):
    row = make_osmo_tx(txinfo, msginfo, "", "", lp_amount, lp_currency)
    row.comment = "lp unstake (period_lock_id: {})".format(period_lock_id)
    return row
