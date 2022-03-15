import time
from urllib.parse import quote

from osmo.api_util import APIUtil

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
