from staketaxcsv.common.make_tx import make_swap_tx
from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers


def handle_jupiter_aggregator_v2(exporter, txinfo):
    txinfo.comment = "jupiter_aggregator"

    transfers_in, transfers_out, _ = txinfo.transfers_net

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency, _, _ = transfers_out[0]
        received_amount, received_currency, _, _ = transfers_in[0]
        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        handle_unknown_detect_transfers(exporter, txinfo)
