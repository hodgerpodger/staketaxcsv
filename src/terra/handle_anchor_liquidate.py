from common.make_tx import make_borrow_tx, make_repay_tx
from terra import util_terra
from terra.constants import CUR_UST, MILLION
from terra.make_tx import (
    make_liquidate_tx,
    make_submit_bid_tx,
    make_retract_bid_tx
)

def handle_liquidate(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    # Extract repay amount
    repay_amount_string = from_contract["repay_amount"][1]
    repay_currency_string = from_contract["stable_denom"][0]
    repay_amount, repay_currency = util_terra._amount(repay_amount_string + repay_currency_string)

    # Extract liquidated collateral
    collateral_amount_string = from_contract["collateral_amount"][0]
    collateral_currency_string = from_contract["collateral_token"][0]
    collateral_amount, collateral_currency = util_terra._amount(collateral_amount_string + collateral_currency_string)

    if wallet_address in from_contract["liquidator"]:
        row = make_liquidate_tx(txinfo, repay_amount, repay_currency, collateral_amount, collateral_currency)
    else:
        row = make_liquidate_tx(txinfo, collateral_amount, collateral_currency, repay_amount, repay_currency)
    
    exporter.ingest_row(row)

def handle_submit_bid(exporter, elem, txinfo):
    # Extract bid amount
    transfer = elem["logs"][0]["events_by_type"]["transfer"]
    bid_string = transfer["amount"][0]
    bid_amount, bid_currency = util_terra._amount(bid_string)

    row = make_submit_bid_tx(txinfo, bid_amount, bid_currency)
    exporter.ingest_row(row)

def handle_retract_bid(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet = txinfo.wallet_address

    # Extract bid amount
    transfers_in, _ = util_terra._transfers(elem, wallet, txid)
    print(transfers_in)
    bid_amount, bid_currency = transfers_in[0]
    row = make_retract_bid_tx(txinfo, bid_amount, bid_currency)

    # Extract fee, if any, paid by anchor market contract to fee collector
    fee_collector_address = "terra17xpfvakm2amg962yls6f84z3kell8c5lkaeqfa"
    fee_transfers_in, _ = util_terra._transfers(elem, fee_collector_address, txid)

    if len(fee_transfers_in) > 0:
      fee_amount, fee_currency = transfers_in[0]
      row.fee += fee_amount

    exporter.ingest_row(row)