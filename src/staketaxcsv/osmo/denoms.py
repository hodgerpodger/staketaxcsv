from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo.api_osmosis import get_symbol, get_exponent


def symbol(denom):
    symbols = localconfig.symbols

    if denom in symbols:
        return symbols[denom]

    symbol = get_symbol(denom)

    symbols[denom] = symbol
    return symbol


def exponent(currency):
    exponents = localconfig.exponents

    if currency in exponents:
        return exponents[currency]

    exponent = get_exponent(currency)

    exponents[currency] = exponent
    return exponent
