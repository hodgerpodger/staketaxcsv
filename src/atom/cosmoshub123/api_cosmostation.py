import logging
import time

import requests
from urllib.parse import urlencode
from common.debug_util import use_debug_files
from settings_csv import REPORTS_DIR

LIMIT = 50
INITIAL_ID = 3197873


@use_debug_files(None, REPORTS_DIR)
def _get_txs_legacy(wallet_address, from_id):
    query_params = {
        "limit": LIMIT,
        "from": from_id,
    }
    url = f"https://api.cosmostation.io/v1/account/new_txs/{wallet_address}"

    logging.info("Requesting url=%s?%s", url, urlencode(query_params))
    response = requests.get(url, query_params)
    data = response.json()
    time.sleep(1)

    return data


def get_txs_legacy(wallet_address, from_id=None):
    if from_id is None:
        from_id = INITIAL_ID
    data = _get_txs_legacy(wallet_address, from_id)

    elems = [datum["data"] for datum in data]

    # Get id argument to be used in subsequent query
    next_id = data[-1]["header"]["id"] if len(elems) == LIMIT else None

    return elems, next_id


def get_tx(txid):
    url = f"https://api.cosmostation.io/v1/tx/hash/{txid}"

    logging.info("Requesting url=%s", url)
    response = requests.get(url)
    data = response.json()
    time.sleep(1)

    return data["data"]
