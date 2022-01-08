
import logging
import time
import math
import requests
from settings_csv import ATOM_NODE
LIMIT = 50


def _query(uri_path, query_params={}, sleep_seconds=1):
    url = "{}{}".format(ATOM_NODE, uri_path)

    response = requests.get(url, query_params)
    logging.info("requested url=%s", response.url)

    time.sleep(sleep_seconds)

    return response.json()


def get_tx(txid):
    uri_path = "/cosmos/tx/v1beta1/txs/{}".format(txid)
    query_params = {}

    data = _query(uri_path, query_params)

    return data.get("tx_response", None)


def get_txs_count_pages(address):
    # Number of queries for events message.sender
    _, _, count_sender = get_txs(address, is_sender=True, offset=0, sleep_seconds=0)
    pages_sender = max(math.ceil(count_sender / LIMIT), 1)

    # Number of queries for events transfer.recipient
    _, _, count_receiver = get_txs(address, is_sender=False, offset=0, sleep_seconds=0)
    pages_receiver = max(math.ceil(count_receiver / LIMIT), 1)

    return pages_sender + pages_receiver


def get_txs(address, is_sender, offset=0, sleep_seconds=1):
    uri_path = "/cosmos/tx/v1beta1/txs"
    query_params = {
        "order_by": "ORDER_BY_DESC",
        "pagination.limit": LIMIT,
        "pagination.offset": offset,
        "pagination.count_total": True
    }
    if is_sender:
        query_params["events"] = "message.sender='{}'".format(address)
    else:
        query_params["events"] = "transfer.recipient='{}'".format(address)

    data = _query(uri_path, query_params, sleep_seconds)

    elems = data["tx_responses"]
    next_offset = offset + LIMIT if len(elems) == LIMIT else None
    total_count = int(data["pagination"]["total"])
    return elems, next_offset, total_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    address = "cosmos18qpryc2jgwcx7xaw7j7ze6cfausvf4hmwelx5f"
    offset = 0


    count = get_txs_count_pages(address)
    print("roger count_txs is")
    print(count)
