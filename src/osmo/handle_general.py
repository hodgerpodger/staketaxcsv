
from osmo.make_tx import (
    make_osmo_simple_tx, make_osmo_transfer_in_tx, make_osmo_transfer_out_tx,
    make_osmo_tx
)
from osmo import constants as co
from common.Exporter import TX_TYPE_OSMO_VOTE, TX_TYPE_OSMO_SET_WITHDRAW_ADDRESS
from osmo.handle_unknown import handle_unknown_detect_transfers
from common.Exporter import TX_TYPE_OSMO_SUBMIT_PROPOSAL, TX_TYPE_OSMO_DEPOSIT
from osmo import util_osmo


def handle_failed_tx(exporter, txinfo):
    pass


def handle_simple(exporter, txinfo, msginfo):
    """ Handles tx with 0 transfers """
    tx_type = "_" + util_osmo._msg_type(msginfo)
    row = make_osmo_simple_tx(txinfo, msginfo, tx_type)
    exporter.ingest_row(row)


def handle_simple_outbound(exporter, txinfo, msginfo):
    """ Handles tx with 1 outbound transfer """
    transfers_in, transfers_out = msginfo.transfers
    tx_type = "_" + util_osmo._msg_type(msginfo)

    if len(transfers_in) == 0 and len(transfers_out) == 1:
        amount, currency = transfers_out[0]
        row = make_osmo_tx(txinfo, msginfo, tx_type, amount, currency, "", "")
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_transfer_ibc(exporter, txinfo, msginfo):
    _handle_transfer(exporter, txinfo, msginfo)


def handle_transfer(exporter, txinfo, msginfo):
    _handle_transfer(exporter, txinfo, msginfo)


def _handle_transfer(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency = transfers_in[0]
        row = make_osmo_transfer_in_tx(txinfo, msginfo, amount, currency)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) == 0 and len(transfers_out) == 1:
        amount, currency = transfers_out[0]
        row = make_osmo_transfer_out_tx(txinfo, msginfo, amount, currency)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) == 0 and len(transfers_out) == 0:
        # ibc transfers can come in batches with unrelated transfers
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)
