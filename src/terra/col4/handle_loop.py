from common.make_tx import make_airdrop_tx
from terra import util_terra
from terra.make_tx import make_lp_unstake_tx


def handle_unstake_and_claim(exporter, elem, txinfo):
    txid = txinfo.txid

    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]
    actions = from_contract["action"]
    contract_addresses = from_contract["contract_address"]
    amounts = from_contract.get("amount", None)

    for i in range(len(actions)):
        action = actions[i]
        contract_address = contract_addresses[i]
        amount_string = _align_amounts_to_actions(actions, amounts)[i]

        if action == "transfer":
            # Extract amount/currency for transfer action
            currency = util_terra._lookup_address(contract_address, txid)
            amount = util_terra._float_amount(amount_string, currency)

            if currency == "LOOP":
                row = make_airdrop_tx(txinfo, amount, currency)
            else:
                row = make_lp_unstake_tx(txinfo, amount, currency)

            exporter.ingest_row(row)


def _align_amounts_to_actions(actions, amounts):
    new_amounts = []
    i = 0

    for action in actions:
        if action in ["Unstake"]:
            new_amounts.append('0')
        else:
            new_amounts.append(amounts[i])
            i += 1

    return new_amounts
