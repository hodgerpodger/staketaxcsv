import logging
from json import JSONDecodeError

from staketaxcsv.sol.api_rpc import RpcAPI
from staketaxcsv.sol.constants import CURRENCY_SOL, MILLION, PROGRAMID_STAKE

FEE_THRESHOLD = 0.03

# Cache for storing results of previous is_staking_account() calls
_is_staking_account_cache = {}


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


def account_exists(wallet_address):
    data = RpcAPI.fetch_account(wallet_address)

    if "result" not in data:
        return False, False
    if "error" in data:
        return False, False

    try:
        owner = data["result"]["value"]["owner"]
        if owner == PROGRAMID_STAKE:
            return False, True
        else:
            return True, False
    except (JSONDecodeError, TypeError):
        return False, False


def is_staking_account(wallet_address):
    """Returns True if the address is a staking account, False otherwise, with caching."""
    if wallet_address in _is_staking_account_cache:
        return _is_staking_account_cache[wallet_address]

    _, is_staking = account_exists(wallet_address)
    _is_staking_account_cache[wallet_address] = is_staking
    return is_staking
