from common.make_tx import make_borrow_tx, make_repay_tx, make_swap_tx
from terra import util_terra
from terra.make_tx import make_deposit_collateral_tx, make_withdraw_collateral_tx, make_liquidate_tx
from terra.constants import CUR_UST


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

    try:
        if(from_contract["is_short"][0] == 'true'):
            short_amount_string = data["logs"][0]["events_by_type"]["from_contract"]["return_amount"][0]
            short_amount = util_terra._float_amount(short_amount_string, CUR_UST)
            row = make_swap_tx(txinfo, borrow_amount, borrow_currency, short_amount, CUR_UST)
            exporter.ingest_row(row)
    except Exception:
        pass


def handle_repay_withdraw(exporter, elem, txinfo):
    # Query
    data = elem

    # Extract repay
    from_contract = data["logs"][0]["events_by_type"]["from_contract"]
    burn_amount_string = from_contract["burn_amount"][0]
    repay_amount, repay_currency = util_terra._amount(burn_amount_string)

    row = make_repay_tx(txinfo, repay_amount, repay_currency, z_index=0)
    exporter.ingest_row(row)

    if len(data["logs"]) > 1:
        # Extract withdraw
        from_contract = data["logs"][1]["events_by_type"]["from_contract"]
        withdraw_amount_string = from_contract["withdraw_amount"][0]
        withdraw_amount, withdraw_currency = util_terra._amount(withdraw_amount_string)

        row = make_withdraw_collateral_tx(txinfo, withdraw_amount, withdraw_currency, empty_fee=True, z_index=1)
        exporter.ingest_row(row)


def handle_auction(exporter, elem, txinfo):
    # Query
    data = elem

    # Extract auction
    from_contract = data["logs"][0]["events_by_type"]["from_contract"]
    liquidated_amount_string = from_contract["liquidated_amount"][0]
    liquidated_amount, liquidated_currency = util_terra._amount(liquidated_amount_string)

    # Extract withdraw
    collateral_amount_string = from_contract["return_collateral_amount"][0]
    collateral_amount, collateral_currency = util_terra._amount(collateral_amount_string)

    row = make_liquidate_tx(txinfo, liquidated_amount, liquidated_currency, collateral_amount, collateral_currency)
    exporter.ingest_row(row)
