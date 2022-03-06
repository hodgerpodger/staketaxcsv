import logging

from osmo import util_osmo
from osmo.handle_claim import handle_claim
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.make_tx import (
    make_osmo_lp_deposit_tx,
    make_osmo_lp_stake_tx,
    make_osmo_lp_unstake_tx,
    make_osmo_lp_withdraw_tx,
)


class LockedTokens:
    """ Accounting class for wallet's locked tokens (lp stake/unstake) """

    locked_tokens = {}  # (<wallet_address>, <period_lock_id>) -> (lp_amount, lp_currency)

    @classmethod
    def add_stake(cls, wallet_address, period_lock_id, lp_amount, lp_currency):
        k = (wallet_address, period_lock_id)
        if k in cls.locked_tokens:
            logging.error("add_token() bad condition: should not be duplicate period_lock_id %s", period_lock_id)
            return

        cls.locked_tokens[k] = (lp_amount, lp_currency)

    @classmethod
    def remove_stake(cls, wallet_address, period_lock_id):
        k = (wallet_address, period_lock_id)
        if k not in cls.locked_tokens:
            logging.error("remove_token() bad condition: unable to find period_lock_id=%s", period_lock_id)
            return None, None

        lp_amount, lp_currency = cls.locked_tokens[k]
        del cls.locked_tokens[k]
        return lp_amount, lp_currency


def handle_lp_deposit(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    comment = "lp_deposit"

    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    if len(transfers_in) == 1 and len(transfers_out) == 2:
        lp_amount, lp_currency = transfers_in[0]
        sent_amount1, sent_currency1 = transfers_out[0]
        sent_amount2, sent_currency2 = transfers_out[1]

        # Construct rows (note: only 1 row has fee)
        rows = []
        rows.append(make_osmo_lp_deposit_tx(
            txinfo, msginfo, sent_amount1, sent_currency1, lp_amount / 2, lp_currency))
        rows.append(make_osmo_lp_deposit_tx(
            txinfo, msginfo, sent_amount2, sent_currency2, lp_amount / 2, lp_currency))

        util_osmo._ingest_rows(exporter, rows, comment)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_lp_deposit_partial(exporter, txinfo, msginfo):
    # Only one currency deposited, not two.
    transfers_in, transfers_out = msginfo.transfers
    comment = "lp_deposit"

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        lp_amount, lp_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]

        # Construct rows
        rows = []
        rows.append(
            make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount, sent_currency, lp_amount, lp_currency)
        )

        util_osmo._ingest_rows(exporter, rows, comment)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_lp_withdraw(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    comment = "lp_withdraw"

    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    if len(transfers_in) == 2 and len(transfers_out) == 1:
        lp_amount, lp_currency = transfers_out[0]
        receive_amount1, receive_currency1 = transfers_in[0]
        receive_amount2, receive_currency2 = transfers_in[1]

        # Construct rows (note: only 1 row has fee)
        rows = []
        rows.append(make_osmo_lp_withdraw_tx(
            txinfo, msginfo, lp_amount / 2, lp_currency, receive_amount1, receive_currency1))
        rows.append(make_osmo_lp_withdraw_tx(
            txinfo, msginfo, lp_amount / 2, lp_currency, receive_amount2, receive_currency2))

        util_osmo._ingest_rows(exporter, rows, comment)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


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


def handle_lp_unstake(exporter, txinfo, msginfo):
    wallet_address = txinfo.wallet_address

    period_lock_id = util_osmo._period_lock_id(msginfo)
    lp_amount, lp_currency = LockedTokens.remove_stake(wallet_address, period_lock_id)

    if lp_amount and lp_currency and period_lock_id:
        row = make_osmo_lp_unstake_tx(txinfo, msginfo, lp_amount, lp_currency, period_lock_id)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)
