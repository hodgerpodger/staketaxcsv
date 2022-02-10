from common.make_tx import make_airdrop_tx, make_unknown_tx
from terra import util_terra


def handle_airdrop_pylon(exporter, elem, txinfo):
    """ Handles airdrops from pylon governance contract """
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    actions = from_contract["action"]
    contract_addresses = from_contract["contract_address"]
    amounts = from_contract.get("amount", None)
    if amounts is None:
        # only airdrop update transactions: ignore as there is nothing to do
        return

    count = 0
    for i in range(len(actions)):
        action = actions[i]
        contract_address = contract_addresses[i]
        amount_string = amounts[i - 1] if i > 0 else ""

        if action == "transfer":
            # Extract amount/currency for transfer action
            currency = util_terra._lookup_address(contract_address, txid)
            amount = util_terra._float_amount(amount_string, currency)

            row = make_airdrop_tx(txinfo, amount, currency, empty_fee=count > 0)
            exporter.ingest_row(row)

            # Error checking
            target = from_contract["target"][count]
            assert(target == wallet_address)

            count += 1

    # Handle error condition
    if count == 0:
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)
