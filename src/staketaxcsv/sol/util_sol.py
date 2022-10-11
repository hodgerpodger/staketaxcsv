import logging

from staketaxcsv.sol.constants import CURRENCY_SOL, MILLION

FEE_THRESHOLD = 0.03


def amount_currency(txinfo, amount_string, currency_address):
    if currency_address in txinfo.mints:
        currency = txinfo.mints[currency_address]["currency"]
        decimals = txinfo.mints[currency_address]["decimals"]

        amount = float(amount_string) / (10 ** decimals)
        return amount, currency
    else:
        logging.warning("amount_currency(): currency_address=%s not found.  Using guesstimate.", currency_address)

        amount = float(amount_string) / MILLION
        return amount, currency_address


def detect_fees(_transfers_in, _transfers_out):
    """ Moves small SOL transfer out amount from into fee """
    fee = ""

    # Detect SOL small transfers out and move into fee
    transfers_out = []
    for transfer_out in _transfers_out:
        amount, currency, source, destination = transfer_out

        if currency == CURRENCY_SOL and amount < FEE_THRESHOLD:
            fee = amount
        else:
            transfers_out.append(transfer_out)

    return _transfers_in, transfers_out, fee


def calculate_fee(txinfo):
    """ Returns fee amount for transaction """
    _, transfers_out, _ = txinfo.transfers
    fee_total = 0

    for transfer_out in transfers_out:
        amount, currency, source, destination = transfer_out

        if currency == CURRENCY_SOL and amount < FEE_THRESHOLD:
            fee_total += amount

    if fee_total > 0:
        return fee_total
    else:
        return txinfo.fee_blockchain
