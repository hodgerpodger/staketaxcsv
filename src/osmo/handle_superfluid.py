from osmo.make_tx import make_osmo_simple_tx, make_osmo_lp_stake_tx
from osmo import util_osmo
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.handle_lp import LockedTokens


def handle_delegate(exporter, txinfo, msginfo):
    lock_id = msginfo.message["lock_id"]

    row = make_osmo_simple_tx(txinfo, msginfo)
    row.comment = "(lock_id: {})".format(lock_id)
    exporter.ingest_row(row)


def handle_lp_stake(exporter, txinfo, msginfo):
    wallet_address = txinfo.wallet_address
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        lp_amount, lp_currency = transfers_out[0]
        period_lock_id = util_osmo._period_lock_id(msginfo)
        LockedTokens.add_stake(wallet_address, period_lock_id, lp_amount, lp_currency)

        row = make_osmo_lp_stake_tx(txinfo, msginfo, lp_amount, lp_currency, period_lock_id)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_undelegate_or_unbond(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_out) == 0 and len(transfers_in) == 0:
        period_lock_id = msginfo.message["lock_id"]

        row = make_osmo_simple_tx(txinfo, msginfo)
        row.comment = "(period_lock_id={})".format(period_lock_id)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)
