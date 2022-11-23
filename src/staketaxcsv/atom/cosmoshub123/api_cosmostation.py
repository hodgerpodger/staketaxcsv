import logging
import time

import requests
from urllib.parse import urlencode
from staketaxcsv.common.debug_util import use_debug_files
from staketaxcsv.settings_csv import REPORTS_DIR

LIMIT = 50
INITIAL_ID = 3197873


@use_debug_files(None, REPORTS_DIR)
def _get_txs_legacy(wallet_address, from_id):
    query_params = {
        "limit": LIMIT,
        "from": from_id,
    }
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    url = f"https://api-cosmos.cosmostation.io/v1/account/new_txs/{wallet_address}"

    logging.info("Requesting url=%s?%s", url, urlencode(query_params))
    response = requests.get(url, query_params, headers=headers)
    data = response.json()
    time.sleep(1)

    return data


def get_txs_legacy(wallet_address, from_id=None):
    if from_id is None:
        from_id = INITIAL_ID
    data = _get_txs_legacy(wallet_address, from_id)

    # Transform to data structure congruent to LCD endpoint data
    elems = []
    for datum in data:
        elem = datum["data"]

        # Add timestamp field if missing in "normal" spot (for really old transactions)
        if "timestamp" not in elem:
            elem["timestamp"] = datum["header"]["timestamp"]

        elems.append(elem)

    # Get id argument to be used in subsequent query
    next_id = data[-1]["header"]["id"] if len(elems) == LIMIT else None

    return elems, next_id


def get_tx(txid):
    url = f"https://api-cosmos.cosmostation.io/v1/tx/hash/{txid}"

    logging.info("Requesting url=%s", url)
    response = requests.get(url)
    data = response.json()
    time.sleep(1)

    # Add timestamp field so that data structure is congruent to LCD endpoint data
    if "timestamp" not in data["data"]:
        data["data"]["timestamp"] = data["header"]["timestamp"]

    return data["data"]
