from terra import util_terra
from common.make_tx import make_transfer_in_tx


def handle_action_complete_transfer_wrapped(txinfo, action, row_comment):
    amount_string = action["amount"]
    currency_address = action["contract"]

    currency = util_terra._lookup_address(currency_address, "")
    amount = util_terra._float_amount(amount_string, currency)
    row = make_transfer_in_tx(txinfo, amount, currency)
    row.comment = row_comment
    return [row]
