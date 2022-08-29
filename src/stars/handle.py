from common.make_tx import make_airdrop_tx
import common.ibc.handle


def handle_airdrop(exporter, txinfo, msginfo):
    (transfers_in, _) = msginfo.transfers

    if len(transfers_in) == 1:
        (amount, currency) = transfers_in[0]
        row = make_airdrop_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
    else:
        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return True
