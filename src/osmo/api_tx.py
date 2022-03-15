import time

from osmo.api_util import APIUtil

OSMO_TX_API_NETLOC = "api-osmosis.cosmostation.io"


def _query(uri_path, query_params):
    result = APIUtil.query_get(OSMO_TX_API_NETLOC, uri_path, query_params)
    time.sleep(1)
    return result


def get_tx(txid):
    uri_path = f"/v1/tx/hash/{txid}"

    data = _query(uri_path, {})

    return data["data"]
