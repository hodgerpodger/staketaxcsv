from common.make_tx import make_simple_tx, make_unknown_tx, make_unknown_tx_with_transfer
from terra import util_terra


def handle_unknown(exporter, txinfo):
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)


def handle_simple(exporter, txinfo, tx_type, z_index=0):
    row = make_simple_tx(txinfo, tx_type, z_index)
    exporter.ingest_row(row)


def handle_unknown_detect_transfers(exporter, txinfo, elem):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        handle_unknown(exporter, txinfo)
    elif len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency, _, _ = transfers_out[0]
        received_amount, received_currency, _, _ = transfers_in[0]

        row = make_unknown_tx_with_transfer(
            txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        i = 0
        for sent_amount, sent_currency in transfers_out:
            row = make_unknown_tx_with_transfer(
                txinfo, sent_amount, sent_currency, "", "", empty_fee=(i > 0), z_index=i
            )
            exporter.ingest_row(row)
            i += 1
        for received_amount, received_currency in transfers_in:
            row = make_unknown_tx_with_transfer(
                txinfo, "", "", received_amount, received_currency, empty_fee=(i > 0), z_index=i
            )
            exporter.ingest_row(row)
            i += 1
