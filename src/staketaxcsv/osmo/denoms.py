from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo import api_osmosis
from staketaxcsv.common.ibc import denoms as denoms_common


def amount_currency_from_raw(amount_raw, currency_raw, lcd_node):
    # Try osmosis api
    amt, cur = _amount_currency_from_api_osmosis(amount_raw, currency_raw)
    if amt is not None and cur:
        return amt, cur

    # Fallback to lcd api if not available
    amt2, cur2 = denoms_common.amount_currency_from_raw(amount_raw, currency_raw, lcd_node)
    return amt2, cur2


def _amount_currency_from_api_osmosis(amount_raw, currency_raw):
    if currency_raw in localconfig.token_metadata:
        symbol, decimals = localconfig.token_metadata[currency_raw]
    else:
        symbol, decimals = api_osmosis.get_token_metadata(currency_raw)

        # i.e. USDC.eth.axl -> USDC
        if symbol and "." in symbol:
            symbol = symbol.split(".")[0]

        localconfig.token_metadata[currency_raw] = (symbol, decimals)

    if not symbol or not decimals:
        return None, None

    amount = float(amount_raw) / float(10 ** decimals)
    return amount, symbol
