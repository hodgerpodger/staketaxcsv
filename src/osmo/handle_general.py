
from common.make_tx import (
    make_simple_tx, make_transfer_in_tx, make_transfer_out_tx, make_reward_tx)
from osmo import constants as co
from osmo.make_tx import make_delegate_tx
from common.Exporter import (TX_TYPE_OSMO_VOTE)
from osmo import util_osmo


TX_TYPES_SIMPLE = {
    co.MSG_TYPE_VOTE: TX_TYPE_OSMO_VOTE
}


def handle_failed_tx(exporter, txinfo):
    pass


def handle_simple(exporter, txinfo, message, transfers):
    msg_type = message["@type"]
    tx_type = TX_TYPES_SIMPLE[msg_type]

    row = make_simple_tx(txinfo, tx_type)
    exporter.ingest_row(row)


def handle_delegate(exporter, txinfo, message, transfers):
    denom = message["amount"]["denom"]
    uamount = message["amount"]["amount"]

    currency = util_osmo._denom_to_currency(denom)
    amount = util_osmo._amount(uamount, currency)

    row = make_delegate_tx(txinfo, amount, currency)
    exporter.ingest_row(row)


def handle_withdraw_reward(exporter, txinfo, message, transfers):
    transfers_in, transfers_out = transfers

    assert(len(transfers_out) == 0)

    for amount, currency in transfers_in:
        row = make_reward_tx(txinfo, amount, currency)
        exporter.ingest_row(row)


def handle_transfer_ibc(exporter, txinfo, message, transfers):
    transfers_in, transfers_out = transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency = transfers_in[0]
        row = make_transfer_in_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) == 0 and len(transfers_out) == 1:
        amount, currency = transfers_out[0]
        row = make_transfer_out_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
        return

    raise Exception("Unexpected condition in handle_transfer_ibc()")
