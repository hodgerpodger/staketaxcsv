from staketaxcsv.common.ibc import make_tx


def handle_evm_transfer(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        receive_amt, receive_cur = transfers_in[0]
        row = make_tx.make_transfer_in_tx(txinfo, msginfo, receive_amt, receive_cur)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) == 0 and len(transfers_out) == 1:
        sent_amt, sent_cur = transfers_out[0]
        row = make_tx.make_transfer_out_tx(txinfo, msginfo, sent_amt, sent_cur)
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle message in handle_evm_transfer()")
