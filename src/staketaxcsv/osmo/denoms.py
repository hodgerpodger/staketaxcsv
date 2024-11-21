from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo import api_osmosis
from staketaxcsv.common.ibc import denoms as denoms_common


def amount_currency_from_raw(amount_raw, currency_raw, lcd_node):
    #amt, cur = _symbol_exponent(amount_raw, currency_raw)
    #if amt is not None and cur:
    #    return amt, cur

    amt2, cur2 = denoms_common.amount_currency_from_raw(amount_raw, currency_raw, lcd_node)
    return amt2, cur2


def _symbol_exponent(amount_raw, currency_raw):
    currency = _symbol(currency_raw)
    if currency:
        ex = _exponent(currency)
        if ex:
            amount = float(amount_raw) / float(10 ** ex)
            return amount, currency

    return None, None


def _symbol(denom):
    symbols = localconfig.symbols
    if denom in symbols:
        return symbols[denom]

    sym = api_osmosis.get_symbol(denom)

    symbols[denom] = sym
    return sym


def _exponent(currency):
    exponents = localconfig.exponents
    if currency in exponents:
        return exponents[currency]

    ex = api_osmosis.get_exponent(currency)

    exponents[currency] = ex
    return ex
