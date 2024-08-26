from staketaxcsv.osmo.make_tx import (
    make_osmo_spend_tx, make_osmo_lp_deposit_tx, make_osmo_tx, make_osmo_reward_tx, make_osmo_lp_withdraw_tx)
from staketaxcsv.common.ExporterTypes import TX_TYPE_LEVANA_LP_UNSTAKE


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
    transfers_in, transfers_out = msginfo.transfers

    # Make a name for this lp pool
    # i.e. 'Levana Perps Market - LINK_USDC' -> 'LINK_USDC'
    lp_currency = "LP_LEVANA_" + label.split('-')[-1].strip()

    if ("deposit_liquidity" in execute_contract_message
         and "stake_to_xlp" in execute_contract_message["deposit_liquidity"]):
        # lp deposit (and 'stake')

        if len(transfers_in) == 0 and len(transfers_out) == 1:
            # Find sent amount/currency
            sent_amount, sent_currency = transfers_out[0]

            # Lp shares
            lp_amount = events_by_type["wasm-liquidity-deposit"]["shares"]

            row = make_osmo_lp_deposit_tx(txinfo, msginfo, sent_amount, sent_currency, lp_amount, lp_currency)
            row.comment += f" [levana perps, contract={contract}, sent {sent_amount} {sent_currency}]"
            exporter.ingest_row(row)
            return
    elif "claim_yield" in execute_contract_message:
        # lp reward

        if len(transfers_in) == 1 and len(transfers_out) == 0:
            rec_amount, rec_currency = transfers_in[0]

            row = make_osmo_reward_tx(txinfo, msginfo, rec_amount, rec_currency)
            row.comment += f" [levana perps lp reward, lp_currency={lp_currency}, contract={contract},]"
            exporter.ingest_row(row)
            return
    elif "unstake_xlp" in execute_contract_message:
        # lp unstake (days later will be the lp withdraw)

        if len(transfers_in) == 0 and len(transfers_out) == 0:
            row = make_osmo_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_LEVANA_LP_UNSTAKE)
            lp_amount = execute_contract_message["unstake_xlp"]["amount"]
            row.comment += f"[levana perps lp unstake, lp_currency={lp_currency}, amount={lp_amount} contract={contract}]"
            exporter.ingest_row(row)
            return
    elif "withdraw_liquidity" in execute_contract_message:
        # lp withdraw

        if len(transfers_in) == 1 and len(transfers_out) == 0:
            rec_amount, rec_currency = transfers_in[0]
            lp_amount = execute_contract_message["withdraw_liquidity"]["lp_amount"]
            row = make_osmo_lp_withdraw_tx(txinfo, msginfo, lp_amount, lp_currency, rec_amount, rec_currency)
            row.comment += f"[levana perps lp withdraw, contract={contract}]"
            exporter.ingest_row(row)
            return

    raise Exception("Unable to handle tx in levana.handle_levana_perps_market()")
