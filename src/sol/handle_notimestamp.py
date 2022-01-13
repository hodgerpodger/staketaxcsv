from common.ExporterTypes import TX_TYPE_MISSING_TIMESTAMP
from common.make_tx import make_simple_tx


def is_notimestamp_tx(txinfo):
    if txinfo.timestamp is None or txinfo.timestamp == "":
        return True
    return False


def handle_notimestamp_tx(exporter, txinfo):
    row = make_simple_tx(txinfo, TX_TYPE_MISSING_TIMESTAMP)
    exporter.ingest_row(row)
