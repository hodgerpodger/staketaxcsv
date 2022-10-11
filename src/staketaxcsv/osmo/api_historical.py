import time
from urllib.parse import quote

from staketaxcsv.osmo.api_util import APIUtil

OSMO_HISTORICAL_API_NETLOC = "api-osmosis.imperator.co"


def _query(uri_path, query_params):
    result = APIUtil.query_get(OSMO_HISTORICAL_API_NETLOC, uri_path, query_params)
    time.sleep(1)
    return result


def get_symbol(ibc_address) -> str or None:
    uri_path = "/search/v1/symbol"
    query_params = {"denom": quote(ibc_address)}

    data = _query(uri_path, query_params)

    return data["symbol"] if "symbol" in data else None


def get_exponent(currency):
    uri_path = "/search/v1/exponent"
    query_params = {"symbol": currency}

    data = _query(uri_path, query_params)

    return data["exponent"] if "exponent" in data else None
