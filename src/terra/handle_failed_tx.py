from common.make_tx import make_spend_tx
from terra import util_terra


def handle_failed_tx(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address

    # If wallet is the signer, treat as spend transaction for fee amount (equivalent to no-op tx with fee).
    try:
        sender = elem["tx"]["value"]["msg"][0]["value"]["sender"]
        if sender == wallet_address:
            fee_amount_string = elem["tx"]["value"]["fee"]["amount"][0]["amount"]
            fee_denom = elem["tx"]["value"]["fee"]["amount"][0]["denom"]
            fee_currency = util_terra._denom_to_currency(fee_denom)
            fee_amount = util_terra._float_amount(fee_amount_string, fee_currency)

            txinfo.fee = ""
            txinfo.fee_currency = ""
            txinfo.comment = "failed tx transaction fee"

            row = make_spend_tx(txinfo, fee_amount, fee_currency)
            exporter.ingest_row(row)
            return
    except Exception:
        pass

    # Otherwise no transaction (no-op transaction with no fee = no transaction)
    pass
