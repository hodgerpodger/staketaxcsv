from staketaxcsv.osmo.make_tx import make_osmo_reward_tx


def handle(exporter, txinfo, msginfo):
    wasm = msginfo.wasm

    action = wasm[0]["action"]

    if action == "claim_user_rewards":
        transfers_in, transfers_out = msginfo.transfers

        if len(transfers_in) > 0 and len(transfers_out) == 0:
            for amt, cur in transfers_in:
                row = make_osmo_reward_tx(txinfo, msginfo, amt, cur)
                exporter.ingest_row(row)
            return

    raise Exception("Unable to handle tx in handle_quasar.handle()")
