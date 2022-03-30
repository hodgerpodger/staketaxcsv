import json
import logging
import math
import os
import requests
import time
from urllib.parse import urlencode
from settings_csv import REPORTS_DIR
from common.debug_util import use_debug_files

TXS_LIMIT_PER_QUERY = 50
EVENTS_TYPE_SENDER = "sender"
EVENTS_TYPE_RECIPIENT = "recipient"
EVENTS_TYPE_SIGNER = "signer"
EVENTS_TYPE_LIST_DEFAULT = [
    EVENTS_TYPE_SENDER,
    EVENTS_TYPE_RECIPIENT,
]


class LcdAPI:
    session = requests.Session()
    debug = False

    def __init__(self, node):
        self.node = node

    def _query(self, uri_path, query_params, sleep_seconds=0):
        url = f"{self.node}{uri_path}"
        logging.info("Requesting url %s?%s ...", url, urlencode(query_params))
        response = self.session.get(url, params=query_params)

        if sleep_seconds:
            time.sleep(sleep_seconds)
        return response.json()

    def get_tx(self, txid):
        uri_path = f"/cosmos/tx/v1beta1/txs/{txid}"
        data = self._query(uri_path, {}, sleep_seconds=1)
        return data.get("tx_response", None)

    def _account_exists(self, wallet_address):
        uri_path = f"/cosmos/auth/v1beta1/accounts/{wallet_address}"
        data = self._query(uri_path, {})
        return data

    def account_exists(self, wallet_address):
        data = self._account_exists(wallet_address)
        if "account" in data:
            return True
        else:
            return False

    @use_debug_files(None, REPORTS_DIR)
    def _get_txs(self, wallet_address, events_type, offset, limit, sleep_seconds):
        uri_path = "/cosmos/tx/v1beta1/txs"
        query_params = {
            "order_by": "ORDER_BY_DESC",
            "pagination.limit": limit,
            "pagination.offset": offset,
            "pagination.count_total": True,
        }
        if events_type == EVENTS_TYPE_SENDER:
            query_params["events"] = f"message.sender='{wallet_address}'"
        elif events_type == EVENTS_TYPE_RECIPIENT:
            query_params["events"] = f"transfer.recipient='{wallet_address}'"
        elif events_type == EVENTS_TYPE_SIGNER:
            query_params["events"] = f"message.signer='{wallet_address}'"
        else:
            raise Exception("Add case for events_type: {}".format(events_type))

        data = self._query(uri_path, query_params, sleep_seconds)

        return data

    def get_txs(self, wallet_address, events_type, offset=0, limit=TXS_LIMIT_PER_QUERY, sleep_seconds=1):
        data = self._get_txs(wallet_address, events_type, offset, limit, sleep_seconds)

        # No results or error
        if data.get("code") == 3:
            return [], None, 0

        elems = data["tx_responses"]
        next_offset = offset + limit if len(elems) == limit else None
        total_count_txs = int(data["pagination"]["total"])
        return elems, next_offset, total_count_txs

    def _get_ibc_symbol(self, ibc_address):
        """ 'ibc/0471F1C4E7AFD3F07702BEF6DC365268D64570F7C1FDC98EA6098DD6DE59817B' -> 'OSMO' """
        _, hash = ibc_address.split("/")
        uri_path = "/ibc/apps/transfer/v1/denom_traces/{}".format(hash)
        query_params = {}

        data = self._query(uri_path, query_params, sleep_seconds=1)
        return data

    def get_ibc_symbol(self, ibc_address):
        data = self._get_ibc_symbol(ibc_address)
        denom = data["denom_trace"]["base_denom"]
        symbol = denom[1:].upper()  # i.e. "uosmo" -> "OSMO"
        return symbol


def get_txs_all(node, wallet_address, progress, max_txs, limit=TXS_LIMIT_PER_QUERY, sleep_seconds=1,
                debug=False, stage_name="default", events_types=None):
    LcdAPI.debug = debug
    api = LcdAPI(node)
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT
    max_pages = math.ceil(max_txs / limit)

    out = []
    page_for_progress = 1
    for events_type in events_types:
        offset = 0

        for _ in range(0, max_pages):
            message = f"Fetching page {page_for_progress} for {events_type} ..."
            progress.report(page_for_progress, message, stage_name)
            page_for_progress += 1

            elems, offset, _ = api.get_txs(wallet_address, events_type, offset, limit, sleep_seconds)

            out.extend(elems)
            if offset is None:
                break

    out = _remove_duplicates(out)
    return out


def _remove_duplicates(elems):
    out = []
    txids = set()

    for elem in elems:
        if elem["txhash"] in txids:
            continue

        out.append(elem)
        txids.add(elem["txhash"])

    out.sort(key=lambda elem: elem["timestamp"], reverse=True)
    return out


def get_txs_pages_count(node, address, max_txs, limit=TXS_LIMIT_PER_QUERY, debug=False,
                        events_types=None):
    LcdAPI.debug = debug
    api = LcdAPI(node)
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT

    total_pages = 0
    for event_type in events_types:
        # Number of queries for events message.sender
        _, _, num_txs = api.get_txs(address, event_type, offset=0, limit=limit, sleep_seconds=0)
        num_txs = min(num_txs, max_txs)
        num_pages = math.ceil(num_txs / limit) if num_txs else 1

        logging.info("event_type: %s, num_txs: %s, num_pages: %s", event_type, num_txs, num_pages)
        total_pages += num_pages

    return total_pages


def get_ibc_ticker(node, ibc_address, cache_ibc_addresses=None):
    if cache_ibc_addresses is not None and ibc_address in cache_ibc_addresses:
        return cache_ibc_addresses[ibc_address]

    symbol = LcdAPI(node).get_ibc_symbol(ibc_address)

    if cache_ibc_addresses is not None:
        cache_ibc_addresses[ibc_address] = symbol
    return symbol
