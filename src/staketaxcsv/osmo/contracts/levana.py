from staketaxcsv.osmo.make_tx import make_osmo_spend_tx, make_osmo_lp_deposit_tx


def handle_update_price_feeds(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 0 and len(transfers_out) == 1:
        sent_amount, sent_currency = transfers_out[0]
        row = make_osmo_spend_tx(txinfo, msginfo, sent_amount, sent_currency)
        row.comment += "[spend tx for update price feeds cost]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in levana.handle_update_price_feeds()")


def handle_levana_perps_market(exporter, txinfo, msginfo, label):
    execute_contract_message = msginfo.execute_contract_message
    contract = msginfo.contract
    events_by_type = msginfo.events_by_type

    if ("deposit_liquidity" in execute_contract_message and
        "stake_to_xlp" in execute_contract_message["deposit_liquidity"]):
        transfers_in, transfers_out = msginfo.transfers
        if len(transfers_in) == 0 and len(transfers_out) == 1:
            # Find sent amount/currency
            sent_amount, sent_currency = transfers_out[0]

            # Lp shares
            lp_amount = events_by_type["wasm-liquidity-deposit"]["shares"]

            # Make a name for this lp pool
            # i.e. 'Levana Perps Market - LINK_USDC' -> 'LINK_USDC'
            lp_currency = "LP_LEVANA_" + label.split('-')[-1].strip()

            row = make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount, sent_currency, lp_amount, lp_currency)
            row.comment += f" [levana perps, contract={contract}, sent {sent_amount} {sent_currency}]"
            exporter.ingest_row(row)
            return

    raise Exception("Unable to handle tx in levana.handle_levana_perps_market()")
