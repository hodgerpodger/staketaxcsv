from staketaxcsv.osmo.make_tx import make_osmo_swap_tx


def handle_liquid_stake(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        received_amount, received_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]

        row = make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)

        return

    raise Exception("Unable to handle tx in handle_liquid_stake()")
