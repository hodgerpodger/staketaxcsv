# Serum v3 Program: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin

import logging

from common.make_tx import make_swap_tx
from sol.config_sol import localconfig
from sol.make_tx import make_serum_dex_no_transfer, make_serum_dex_transfer_in, make_serum_dex_transfer_out


def handle_serumv3(exporter, txinfo):
    txinfo.comment = "serum_v3"
    txid = txinfo.txid
    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if localconfig.debug:
        logging.info("----------serumv3------------------------------")
        logging.info("serum transaction txid=%s transfers_in:%s transfers_out:%s", txid, transfers_in, transfers_out)

    # Look for swap case
    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency, _, _ = transfers_out[0]
        received_amount, received_currency, _, _ = transfers_in[0]

        if sent_amount == 0 or received_amount == 0:
            pass
        else:
            row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
            exporter.ingest_row(row)
            return

    # Transfers in
    count = 0
    for transfer_in in transfers_in:
        received_amount, received_currency, _, _ = transfer_in
        if received_amount == 0:
            continue

        row = make_serum_dex_transfer_in(txinfo, received_amount, received_currency, empty_fee=(count > 0))
        exporter.ingest_row(row)
        count += 1

    # Transfers out
    for transfer_out in transfers_out:
        sent_amount, sent_currency, _, _ = transfer_out
        if sent_amount == 0:
            continue

        row = make_serum_dex_transfer_out(txinfo, sent_amount, sent_currency, empty_fee=(count > 0))
        exporter.ingest_row(row)
        count += 1

    # Add transaction if none created
    if count == 0:
        row = make_serum_dex_no_transfer(txinfo)
        exporter.ingest_row(row)
