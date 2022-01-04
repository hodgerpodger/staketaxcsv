
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.make_tx import (make_osmo_lp_deposit_tx, make_osmo_lp_withdraw_tx,
                          make_osmo_lp_stake_tx, make_osmo_lp_unstake_tx,
                          make_osmo_transfer_in_tx, make_osmo_transfer_out_tx)
from osmo.config_osmo import localconfig
from osmo import util_osmo
from osmo.handle_claim import handle_claim


def handle_lp_deposit(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    comment = "liquidity pool deposit"

    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    if len(transfers_in) == 1 and len(transfers_out) == 2:
        lp_amount, lp_currency = transfers_in[0]
        sent_amount1, sent_currency1 = transfers_out[0]
        sent_amount2, sent_currency2 = transfers_out[1]

        # Construct rows (note: only 1 row has fee)
        rows = []
        if localconfig.lp:
            # Optional: treat lp deposit as 2 outbound transfers and 1 lp receive token.
            rows.append(make_osmo_transfer_out_tx(txinfo, msginfo, sent_amount1, sent_currency1))
            rows.append(make_osmo_transfer_out_tx(txinfo, msginfo, sent_amount2, sent_currency2))
            rows.append(make_osmo_lp_deposit_tx(txinfo, msginfo, "", "", lp_amount, lp_currency))
        else:
            # Default: 2 _MsgJoinPool rows
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
    comment = "liquidity pool deposit"

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        lp_amount, lp_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]

        # Construct rows
        rows = []
        if localconfig.lp:
            # Optional: treat lp deposit as 1 outbound transfers and 1 lp receive token.
            rows.append(make_osmo_transfer_out_tx(txinfo, msginfo, sent_amount, sent_currency))
            rows.append(make_osmo_lp_deposit_tx(txinfo, msginfo, "", "", lp_amount, lp_currency))
        else:
            # 1 _MsgJoinSwapExternAmountIn row
            rows.append(
                make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount, sent_currency, lp_amount, lp_currency)
            )

        util_osmo._ingest_rows(exporter, rows, comment)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def handle_lp_withdraw(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    comment = "liquidity pool withdraw"

    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    if len(transfers_in) == 2 and len(transfers_out) == 1:
        lp_amount, lp_currency = transfers_out[0]
        receive_amount1, receive_currency1 = transfers_in[0]
        receive_amount2, receive_currency2 = transfers_in[1]

        # Construct rows (note: only 1 row has fee)
        rows = []
        if localconfig.lp:
            # Optional: treat lp withdraw as 2 inbound transfers and 1 lp send token.
            rows.append(make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount, lp_currency, "", ""))
            rows.append(make_osmo_transfer_in_tx(txinfo, msginfo, receive_amount1, receive_currency1))
            rows.append(make_osmo_transfer_in_tx(txinfo, msginfo, receive_amount2, receive_currency2))
        else:
            # Default: 2 _MsgExitPool rows
            rows.append(make_osmo_lp_withdraw_tx(
                txinfo, msginfo, lp_amount / 2, lp_currency, receive_amount1, receive_currency1))
            rows.append(make_osmo_lp_withdraw_tx(
                txinfo, msginfo, lp_amount / 2, lp_currency, receive_amount2, receive_currency2))

        util_osmo._ingest_rows(exporter, rows, comment)
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
