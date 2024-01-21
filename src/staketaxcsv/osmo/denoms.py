from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo import api_osmosis
from staketaxcsv.common.ibc import denoms as denoms_common


def amount_currency_from_raw(amount_raw, currency_raw, lcd_node):
    amount, currency = denoms_common.amount_currency_from_raw(amount_raw, currency_raw, lcd_node)

    if currency.startswith("unknown_"):
        # try osmosis api
        currency2 = _symbol(currency_raw)
        if currency2:
            ex = _exponent(currency2)
            if ex:
                amount2 = float(amount_raw) / float(10 ** ex)
                return amount2, currency2

    return amount, currency


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
