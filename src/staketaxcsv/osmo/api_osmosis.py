import time
from urllib.parse import quote

from staketaxcsv.osmo.api_util import APIUtil

OSMO_API_NETLOC = "sqsprod.osmosis.zone"


def _query(uri_path, query_params):
    result = APIUtil.query_get(OSMO_API_NETLOC, uri_path, query_params)
    time.sleep(1)
    return result


def get_token_metadata(ibc_address) -> str or None:
    uri_path = "/tokens/metadata"
    query_params = {"denoms": quote(ibc_address)}

    data = _query(uri_path, query_params)

    symbol = data.get(ibc_address, {}).get("symbol", None)
    decimals = data.get(ibc_address, {}).get("decimals", None)

    if symbol and decimals:
        return symbol, decimals
    else:
        return None, None
