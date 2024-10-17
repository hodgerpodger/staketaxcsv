import staketaxcsv.common.make_tx


def is_astroport_pair_contract(contract_data):
    return ("contract_info" in contract_data
            and contract_data["contract_info"].get("label") in (
                "Astroport pair", "Astroport LP token", "Astroport Router"))


def handle_astroport_swap(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net
    wasm = msginfo.wasm

    if len(transfers_in) == 1 and len(transfers_out) == 1 and wasm[0]["action"] == "swap":
        sent_amount, sent_currency = transfers_out[0]
        receive_amount, receive_currency = transfers_in[0]
        row = staketaxcsv.common.make_tx.make_swap_tx(
            txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
        exporter.ingest_row(row)
    else:
        raise Exception("Unable to handle tx in handle_astroport_swap()")
