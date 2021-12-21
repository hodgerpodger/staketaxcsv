
from osmo.handle_unknown import handle_unknown_detect_transfers
from common.make_tx import make_swap_tx


def handle_swap(exporter, txinfo, message, transfers):
    transfers_in, transfers_out = transfers

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency = transfers_out[0]
        received_amount, received_currency = transfers_in[0]

        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, transfers)
