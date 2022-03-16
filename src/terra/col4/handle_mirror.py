from common.make_tx import make_transfer_out_tx, make_transfer_in_tx
from terra import util_terra
from terra.make_tx import make_submit_limit_order

def handle_submit_limit_order(exporter, elem, txinfo):
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]
    ask_amount, ask_currency = util_terra._amount(from_contract["ask_asset"][0])
    offer_amount, offer_currency = util_terra._amount(from_contract["offer_asset"][0])
    row = make_submit_limit_order(txinfo, ask_amount, ask_currency, offer_amount, offer_currency)
    exporter.ingest_row(row)