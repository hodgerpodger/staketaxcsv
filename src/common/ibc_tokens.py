
import atom.api_lcd
import terra.api_lcd
from settings_csv import TICKER_ATOM, TICKER_LUNA


def get_symbol(localconfig, ticker, ibc_address):
    if ibc_address in localconfig.ibc_addresses:
        return localconfig.ibc_addresses[ibc_address]

    symbol = _get_symbol(ticker, ibc_address)

    localconfig.ibc_addresses[ibc_address] = symbol
    return symbol


def _get_symbol(ticker, ibc_address):
    """ 'ibc/0471F1C4E7AFD3F07702BEF6DC365268D64570F7C1FDC98EA6098DD6DE59817B' -> 'OSMO' """
    _, hash = ibc_address.split("/")
    uri = "/ibc/apps/transfer/v1/denom_traces/{}".format(hash)

    if ticker == TICKER_LUNA:
        data = terra.api_lcd._query(uri, {})
    elif ticker == TICKER_ATOM:
        data = atom.api_lcd._query(uri, {})
    else:
        raise Exception("get_symbol(): bad ticker={}".format(ticker))

    denom = data["denom_trace"]["base_denom"]
    symbol = denom[1:].upper()  # i.e. "uosmo" -> "OSMO"

    return symbol
