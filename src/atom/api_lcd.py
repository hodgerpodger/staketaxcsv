import logging
import math
import time

import requests
from settings_csv import ATOM_NODE
from urllib.parse import urlencode

LIMIT_PER_QUERY = 50


def _query(uri_path, query_params, sleep_seconds=1):
    url = f"{ATOM_NODE}{uri_path}"
    logging.info("Requesting url %s?%s", url, urlencode(query_params))
    response = requests.get(url, query_params)

    time.sleep(sleep_seconds)
    return response.json()


def get_tx(txid):
    uri_path = f"/cosmos/tx/v1beta1/txs/{txid}"
    data = _query(uri_path, {})
    return data.get("tx_response", None)


def _account_exists(wallet_address):
    uri_path = f"/cosmos/auth/v1beta1/accounts/{wallet_address}"
    data = _query(uri_path, {})
    return data


def account_exists(wallet_address):
    data = _account_exists(wallet_address)

    if "account" in data and data.get("account").get("account_number", None):
        return True
    else:
        return False


def _get_txs(wallet_address, is_sender, offset, sleep_seconds):
    uri_path = "/cosmos/tx/v1beta1/txs"
    query_params = {
        "order_by": "ORDER_BY_DESC",
        "pagination.limit": LIMIT_PER_QUERY,
        "pagination.offset": offset,
        "pagination.count_total": True,
    }
    if is_sender:
        query_params["events"] = f"message.sender='{wallet_address}'"
    else:
        query_params["events"] = f"transfer.recipient='{wallet_address}'"

    data = _query(uri_path, query_params, sleep_seconds)
    return data


def get_txs(wallet_address, is_sender, offset=0, sleep_seconds=1):
    data = _get_txs(wallet_address, is_sender, offset, sleep_seconds)

    # No results or error
    if data.get("code") == 3:
        return [], None, 0

    elems = data["tx_responses"]
    next_offset = offset + LIMIT_PER_QUERY if len(elems) == LIMIT_PER_QUERY else None
    total_count = int(data["pagination"]["total"])
    return elems, next_offset, total_count


def get_txs_count_pages(address):
    # Number of queries for events message.sender
    _, _, count_sender = get_txs(address, is_sender=True, offset=0, sleep_seconds=0)
    pages_sender = max(math.ceil(count_sender / LIMIT_PER_QUERY), 1)

    # Number of queries for events transfer.recipient
    _, _, count_receiver = get_txs(address, is_sender=False, offset=0, sleep_seconds=0)
    pages_receiver = max(math.ceil(count_receiver / LIMIT_PER_QUERY), 1)

    logging.info("pages_sender: %s pages_receiver: %s", pages_sender, pages_receiver)

    return pages_sender + pages_receiver
