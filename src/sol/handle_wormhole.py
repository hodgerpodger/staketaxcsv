from common.ExporterTypes import TX_TYPE_SOL_WORMHOLE_NOOP
from common.make_tx import make_simple_tx, make_transfer_in_tx, make_transfer_out_tx
from sol.handle_simple import handle_unknown_detect_transfers


def handle_wormhole(exporter, txinfo):
    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        # various wormhole internal setup transaction
        row = make_simple_tx(txinfo, TX_TYPE_SOL_WORMHOLE_NOOP)
        exporter.ingest_row(row)
    elif len(transfers_in) == 1 and len(transfers_out) == 0:
        # actual wormhole transfer in
        received_amount, received_currency, _, _ = transfers_in[0]
        row = make_transfer_in_tx(txinfo, received_amount, received_currency)
        exporter.ingest_row(row)
    elif len(transfers_out) == 1 and len(transfers_in) == 0:
        # actual wormhole transfer out
        sent_amount, sent_currency, _, dest = transfers_out[0]
        row = make_transfer_out_tx(txinfo, sent_amount, sent_currency, dest)
        exporter.ingest_row(row)
    else:
        handle_unknown_detect_transfers(exporter, txinfo)
