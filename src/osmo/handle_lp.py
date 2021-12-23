
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.make_tx import (make_osmo_lp_deposit_tx, make_osmo_lp_withdraw_tx,
    make_osmo_lp_stake_tx, make_osmo_lp_unstake_tx)


def handle_lp_deposit(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 2:
        lp_amount, lp_currency = transfers_in[0]

        i = 0
        for sent_amount, sent_currency in transfers_out:
            row = make_osmo_lp_deposit_tx(
                txinfo, msginfo, sent_amount, sent_currency, lp_amount / 2, lp_currency, empty_fee=(i > 0))
            exporter.ingest_row(row)
            i += 1
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_lp_deposit_partial(exporter, txinfo, msginfo):
    # Only one currency deposited, not two.
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        lp_amount, lp_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]
        row = make_osmo_lp_deposit_tx(
            txinfo, msginfo, sent_amount, sent_currency, lp_amount, lp_currency
        )
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_lp_withdraw(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 2 and len(transfers_out) == 1:
        lp_amount, lp_currency = transfers_out[0]

        i = 0
        for receive_amount, receive_currency in transfers_in:
            row = make_osmo_lp_withdraw_tx(
                txinfo, msginfo, lp_amount / 2, lp_currency, receive_amount, receive_currency, empty_fee=(i > 0))
            exporter.ingest_row(row)
            i += 1
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_lp_stake(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        lp_amount, lp_currency = transfers_out[0]
        row = make_osmo_lp_stake_tx(txinfo, msginfo, lp_amount, lp_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_lp_unstake(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_out) == 0 and len(transfers_in) == 1:
        lp_amount, lp_currency = transfers_in[0]
        row = make_osmo_lp_unstake_tx(txinfo, msginfo, lp_amount, lp_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)

