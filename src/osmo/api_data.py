import time

from osmo.api_util import _query_get

OSMO_DATA_API_NETLOC = "api-osmosis-chain.imperator.co"
LIMIT = 25


def _query(uri_path, query_params={}, sleep_seconds=1):
    result = _query_get(OSMO_DATA_API_NETLOC, uri_path, query_params)
    time.sleep(sleep_seconds)
    return result


def get_count_txs(address, sleep_seconds=1):
    uri_path = f"/txs/v1/tx/count/{address}"

    data = _query(uri_path, {}, sleep_seconds)

    return sum(row["count"] for row in data)


def get_txs(address, offset=0):
    uri_path = f"/txs/v1/tx/address/{address}"
    query_params = {
        "limit": LIMIT,
        "offset": offset
    }

    data = _query(uri_path, query_params)

    # Extract "tx_response" (found to be common data across multiple APIs)
    return [row["tx_response"] for row in data]


def get_lp_tokens(address):
    """ Returns list of symbols """
    uri_path = f"/lp/v1/rewards/token/{address}"

    data = _query(uri_path)

    return [kv["token"] for kv in data if kv["token"]]


def get_lp_rewards(address, token):
    uri_path = f"/lp/v1/rewards/historical/{address}/{token}"

    data = _query(uri_path)

    return data
