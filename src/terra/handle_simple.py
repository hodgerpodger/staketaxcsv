
from common.make_tx import make_unknown_tx, make_simple_tx


def handle_unknown(exporter, txinfo):
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)


def handle_simple(exporter, txinfo, tx_type, z_index=0):
    row = make_simple_tx(txinfo, tx_type, z_index)
    exporter.ingest_row(row)
