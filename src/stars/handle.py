from common.make_tx import make_airdrop_tx


def handle_airdrop(exporter, txinfo, msginfo):
    (transfers_in, _) = msginfo.transfers
    (amount, currency) = transfers_in[0]
    row = make_airdrop_tx(txinfo, amount, currency)
    exporter.ingest_row(row)
