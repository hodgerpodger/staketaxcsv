from common.make_tx import make_borrow_tx, make_repay_tx
from terra import util_terra
from terra.constants import CUR_UST, MILLION
from terra.make_tx import make_deposit_collateral_tx, make_withdraw_collateral_tx


def handle_deposit_collateral(exporter, elem, txinfo):
    txid = txinfo.txid

    # 1st message: deposit_collateral
    # 2nd message: lock_collateral

    # Parse lock_collateral message
    execute_msg = util_terra._execute_msg(elem, 1)
    collaterals = execute_msg["lock_collateral"]["collaterals"]
    collateral = collaterals[0]
    currency_address, amount = collateral[0], collateral[1]
    assert(len(collaterals) == 1)

    sent_currency = util_terra._lookup_address(currency_address, txid)
    sent_amount = util_terra._float_amount(amount, sent_currency)

    row = make_deposit_collateral_tx(txinfo, sent_amount, sent_currency)
    exporter.ingest_row(row)


def handle_withdraw_collateral(exporter, elem, txinfo):
    txid = txinfo.txid

    # 1st message: unlock_collateral
    # 2nd message: withdraw_collateral

    # Parse unlock_collateral execute_msg
    execute_msg = util_terra._execute_msg(elem, 0)
    collaterals = execute_msg["unlock_collateral"]["collaterals"]
    collateral = collaterals[0]
    currency_address, amount = collateral[0], collateral[1]
    assert (len(collaterals) == 1)

    received_currency = util_terra._lookup_address(currency_address, txid)
    received_amount = util_terra._float_amount(amount, received_currency)

    row = make_withdraw_collateral_tx(txinfo, received_amount, received_currency)
    exporter.ingest_row(row)


def handle_borrow(exporter, elem, txinfo):
    txid = txinfo.txid

    # Extract fee paid by anchor market contract to fee collector
    fee_collector_address = "terra17xpfvakm2amg962yls6f84z3kell8c5lkaeqfa"
    transfers_in, _ = util_terra._transfers(elem, fee_collector_address, txid)
    fee_amount, fee_currency = transfers_in[0]

    # Extract borrow amount
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]
    borrow_amount = float(from_contract["borrow_amount"][0]) / MILLION

    row = make_borrow_tx(txinfo, borrow_amount, CUR_UST)
    row.fee += fee_amount

    exporter.ingest_row(row)


def handle_repay(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)
    amount, currency = transfers_out[0]

    row = make_repay_tx(txinfo, amount, currency)
    exporter.ingest_row(row)
