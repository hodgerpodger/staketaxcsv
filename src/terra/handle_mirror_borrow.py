from common.make_tx import make_borrow_tx, make_repay_tx
from terra import util_terra
from terra.make_tx import make_deposit_collateral_tx, make_withdraw_collateral_tx


def handle_deposit_borrow(exporter, elem, txinfo):
    # Query
    data = elem
    from_contract = data["logs"][0]["events_by_type"]["from_contract"]

    # Extract deposit
    collateral_amount_string = from_contract["collateral_amount"][0]
    deposit_amount, deposit_currency = util_terra._amount(collateral_amount_string)

    # Extract borrow
    mint_amount_string = from_contract["mint_amount"][0]
    borrow_amount, borrow_currency = util_terra._amount(mint_amount_string)

    row = make_deposit_collateral_tx(txinfo, deposit_amount, deposit_currency, z_index=0)
    exporter.ingest_row(row)
    row = make_borrow_tx(txinfo, borrow_amount, borrow_currency, empty_fee=True, z_index=1)
    exporter.ingest_row(row)


def handle_repay_withdraw(exporter, elem, txinfo):
    # Query
    data = elem

    # Extract repay
    from_contract = data["logs"][0]["events_by_type"]["from_contract"]
    burn_amount_string = from_contract["burn_amount"][0]
    repay_amount, repay_currency = util_terra._amount(burn_amount_string)

    # Extract withdraw
    from_contract = data["logs"][1]["events_by_type"]["from_contract"]
    withdraw_amount_string = from_contract["withdraw_amount"][0]
    withdraw_amount, withdraw_currency = util_terra._amount(withdraw_amount_string)

    row = make_repay_tx(txinfo, repay_amount, repay_currency, z_index=0)
    exporter.ingest_row(row)
    row = make_withdraw_collateral_tx(txinfo, withdraw_amount, withdraw_currency, empty_fee=True, z_index=1)
    exporter.ingest_row(row)
