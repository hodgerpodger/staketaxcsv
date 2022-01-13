from common.make_tx import make_swap_tx
from sol.handle_simple import handle_unknown_detect_transfers


def handle_marinade(exporter, txinfo):
    txinfo.comment = "marinade_finance"

    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if len(transfers_in) == 1 and len(transfers_out) == 1 and len(transfers_unknown) == 0:
        received_amount, received_currency, _, _ = transfers_in[0]
        sent_amount, sent_currency, _, _ = transfers_out[0]
        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo)
