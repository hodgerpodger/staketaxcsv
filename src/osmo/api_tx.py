
import time
from osmo.api_util import _query_get
OSMO_TX_API_NETLOC = "api-osmosis.cosmostation.io"


def _query(netloc, uri_path, query_params):
    result = _query_get(netloc, uri_path, query_params)
    time.sleep(1)
    return result


def get_tx(txid):
    template = "/v1/tx/hash/{txid}"
    uri_path = template.format(txid=txid)
    query_params = {}

    data = _query(OSMO_TX_API_NETLOC, uri_path, query_params)

    return data["data"]
