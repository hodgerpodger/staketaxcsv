from osmo.make_tx import make_osmo_simple_tx

def handle_delegate(exporter, txinfo, msginfo):
    lock_id = msginfo.message["lock_id"]

    row = make_osmo_simple_tx(txinfo, msginfo)
    row.comment = "(lock_id: {})".format(lock_id)
    exporter.ingest_row(row)
