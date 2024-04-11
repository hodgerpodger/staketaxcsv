from staketaxcsv.osmo.make_tx import make_osmo_reward_tx


def handle_claim_rewards(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        received_amount, received_currency = transfers_in[0]

        row = make_osmo_reward_tx(txinfo, msginfo, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in handle_claim_rewards()")
