
from common.make_tx import make_unknown_tx, make_unknown_tx_with_transfer


def handle_unknown_detect_transfers(exporter, txinfo, transfers):
    transfers_in, transfers_out = transfers

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        handle_unknown(exporter, txinfo)
        return
    elif len(transfers_in) == 1 and len(transfers_out) == 1:
        # Present unknown transaction as one line (for this special case).
        sent_amount, sent_currency = transfers_out[0]
        received_amount, received_currency = transfers_in[0]

        row = make_unknown_tx_with_transfer(
            txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        # Present unknown transaction as separate transfers.
        i = 0
        for sent_amount, sent_currency in transfers_out:
            row = make_unknown_tx_with_transfer(
                txinfo, sent_amount, sent_currency, "", "", empty_fee=(i > 0), z_index=i
            )
            exporter.ingest_row(row)
            i += 1
        for received_amount, received_currency in transfers_in:
            row = make_unknown_tx_with_transfer(
                txinfo, "", "", received_amount, received_currency, empty_fee=(i > 0), z_index=i
            )
            exporter.ingest_row(row)
            i += 1


def handle_unknown(exporter, txinfo):
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)
