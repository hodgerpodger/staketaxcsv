
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.make_tx import make_osmo_swap_tx
from osmo.handle_claim import handle_claim


def handle_swap(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    # Remove intermediate swap tokens (A -> B -> C; remove B)
    transfers_common = set(transfers_in).intersection(set(transfers_out))
    for t in transfers_common:
        transfers_in.remove(t)
        transfers_out.remove(t)

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency = transfers_out[0]
        received_amount, received_currency = transfers_in[0]

        row = make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)
