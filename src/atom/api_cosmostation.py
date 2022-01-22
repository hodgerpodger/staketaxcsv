import logging
import requests
import time

LIMIT = 250
INITIAL_ID = 3197873


def get_txs_legacy(wallet_address, id=None):
    if id is None:
        id = INITIAL_ID
    query_params = {
        "limit": LIMIT,
        "from": id,
    }
    url = "https://api.cosmostation.io/v1/account/new_txs/{}".format(wallet_address)

    logging.info("Requesting url=%s", url)
    response = requests.get(url, query_params)
    data = response.json()
    time.sleep(1)

    # Filter to only cosmoshub-3 transactions
    elems = [datum["data"] for datum in data if datum["header"]["chain_id"] == "cosmoshub-3"]

    # Get id argument to be used in subsequent query
    next_id = data[-1]["header"]["id"] if len(elems) == LIMIT else None

    return elems, next_id


def get_tx(txid):
    url = "https://api.cosmostation.io/v1/tx/hash/{}".format(txid)

    logging.info("Requesting url=%s", url)
    response = requests.get(url)
    data = response.json()
    time.sleep(1)

    return data["data"]



