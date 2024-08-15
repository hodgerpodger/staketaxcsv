from staketaxcsv.common.make_tx import make_spend_tx
from staketaxcsv.osmo.make_tx import make_osmo_tx
from staketaxcsv.common.ExporterTypes import TX_TYPE_OSMO_ICNS


def handle(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if msginfo.msg_index == 0 and len(transfers_in) == 0 and len(transfers_out) == 1:
        sent_amt, sent_cur = transfers_out[0]

        row = make_spend_tx(txinfo, sent_amt, sent_cur)
        row.comment = "[spend fee for icns]"
        exporter.ingest_row(row)
        return
    else:
        row = make_osmo_tx(txinfo, msginfo, "", "", "", "", txid=None, empty_fee=True, tx_type=TX_TYPE_OSMO_ICNS)
        exporter.ingest_row(row)
