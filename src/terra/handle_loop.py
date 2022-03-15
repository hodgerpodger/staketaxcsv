from common.ErrorCounter import ErrorCounter
from common.make_tx import make_transfer_in_tx, make_transfer_out_tx, make_airdrop_tx
from terra import util_terra
from terra.handle_simple import handle_unknown, handle_unknown_detect_transfers
from terra.make_tx import make_lp_unstake_tx


def handle_unstake_and_claim(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]
    actions = from_contract["action"]
    contract_addresses = from_contract["contract_address"]
    amounts = from_contract.get("amount", None)

    count = 0
    for i in range(len(actions)):
        action = actions[i]
        contract_address = contract_addresses[i]
        amount_string = util_terra._align_amounts_to_actions(actions, amounts)[i]

        if action == "transfer":
            # Extract amount/currency for transfer action
            currency = util_terra._lookup_address(contract_address, txid)
            amount = util_terra._float_amount(amount_string, currency)

            if currency == "LOOP":
                row = make_airdrop_tx(txinfo, amount, currency)
            else:
                row = make_lp_unstake_tx(txinfo, amount, currency)

            exporter.ingest_row(row)