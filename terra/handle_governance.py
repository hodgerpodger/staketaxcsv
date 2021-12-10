
from terra.make_tx import make_gov_stake_tx, make_gov_unstake_tx
from terra import util_terra


def handle_governance_stake(exporter, elem, txinfo):
    txid = txinfo.txid

    # Get currency
    currency_address = util_terra._contract(elem)
    currency, _ = util_terra._lookup_address(currency_address, txid)

    # Get amount
    execute_msg = util_terra._execute_msg(elem)
    amount_string = execute_msg["send"]["amount"]
    amount = util_terra._float_amount(amount_string, currency)

    row = make_gov_stake_tx(txinfo, amount, currency)
    exporter.ingest_row(row)


def handle_governance_unstake(exporter, elem, txinfo):
    txid = txinfo.txid

    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    actions = from_contract["action"]
    amounts = from_contract["amount"]
    contract_addresses = from_contract["contract_address"]

    for i in range(len(actions)):
        action = actions[i]
        amount_string = amounts[i]
        contract_address = contract_addresses[i]

        if action == "transfer":
            currency, _ = util_terra._lookup_address(contract_address, txid)
            amount = util_terra._float_amount(amount_string, currency)

            row = make_gov_unstake_tx(txinfo, amount, currency)
            exporter.ingest_row(row)


def _get_received_currency_address(elem, txid):

    events = elem["logs"][0]["events"]
    for event in events:
        if event["type"] == "execute_contract":
            attributes = event["attributes"]

            currency_address = attributes[1]["value"]
            return currency_address

    raise Exception("Bad condition _get_received_currency_address() txid={}".format(txid))
