import json
import logging
import math
import os
import time
from urllib.parse import urlencode

import requests
from dateutil import parser
from staketaxcsv.common.debug_util import use_debug_files
from staketaxcsv.common.ibc.api_common import (
    EVENTS_TYPE_LIST_DEFAULT,
    EVENTS_TYPE_RECIPIENT,
    EVENTS_TYPE_SENDER,
    EVENTS_TYPE_SIGNER,
)
from staketaxcsv.fet.config_fet import localconfig
from staketaxcsv.settings_csv import REPORTS_DIR

TXS_LIMIT_PER_QUERY = 50


class FetRpcAPI:
    session = requests.Session()

    def __init__(self, node):
        self.node = node

    def _query(self, uri_path, query_params, sleep_seconds=0):
        url = f"{self.node}{uri_path}"
        logging.info("Requesting url %s?%s ...", url, urlencode(query_params))
        response = self.session.get(url, params=query_params)

        if sleep_seconds:
            time.sleep(sleep_seconds)
        return response.json()

    @use_debug_files(localconfig, REPORTS_DIR)
    def _txs_search(self, wallet_address, events_type, page, per_page, node):
        # Note unused node variable just a hack to make @use_debug_file work without modifications
        uri_path = "/tx_search"
        query_params = {"page": page, "per_page": per_page}
        if events_type == EVENTS_TYPE_SENDER:
            query_params["query"] = "\"message.sender='{}'\"".format(wallet_address)
        elif events_type == EVENTS_TYPE_RECIPIENT:
            query_params["query"] = "\"transfer.recipient='{}'\"".format(wallet_address)
        elif events_type == EVENTS_TYPE_SIGNER:
            query_params["query"] = "\"message.signer='{}'\"".format(wallet_address)
        else:
            raise Exception("Add case for events_type: {}".format(events_type))

        data = self._query(uri_path, query_params, sleep_seconds=1)

        return data

    def txs_search(self, wallet_address, events_type, page, per_page):
        data = self._txs_search(wallet_address, events_type, page, per_page, self.node)

        elems = data["result"]["txs"]
        total_count_txs = int(data["result"]["total_count"])
        total_count_pages = math.ceil(total_count_txs / per_page)
        if page >= total_count_pages:
            next_page = None
        else:
            next_page = page + 1

        return elems, next_page, total_count_pages, total_count_txs

    def _tx(self, txid):
        uri_path = "/tx"
        query_params = {"hash": "0x{}".format(txid)}

        data = self._query(uri_path, query_params)
        return data

    def tx(self, txid):
        data = self._tx(txid)

        elem = data.get("result", None)
        return elem

    @use_debug_files(localconfig, REPORTS_DIR)
    def _block(self, height):
        uri_path = "/block"
        query_params = {"height": height}

        data = self._query(uri_path, query_params, sleep_seconds=0.2)

        return data

    def block_time(self, height):
        data = self._block(height)

        # i.e. "2021-08-26T21:08:44.86954814Z" -> "2021-08-26 21:08:44"
        ts = data["result"]["block"]["header"]["time"]
        timestamp = parser.parse(ts).strftime("%Y-%m-%d %H:%M:%S")
        return timestamp


def get_txs_all(node, wallet_address, progress, max_txs, per_page=TXS_LIMIT_PER_QUERY, debug=False,
                stage_name="default", events_types=None):
    api = FetRpcAPI(node)
    api.debug = debug
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT
    max_pages = math.ceil(max_txs / per_page)

    out = []
    page_for_progress = 1
    for events_type in events_types:
        for page in range(1, max_pages + 1):
            message = f"Fetching page {page_for_progress} ..."
            progress.report(page_for_progress, message, stage_name)
            page_for_progress += 1

            elems, next_page, _, _ = api.txs_search(wallet_address, events_type, page, per_page)

            out.extend(elems)
            if next_page is None:
                break

    out = _remove_duplicates(out)
    return out


def _remove_duplicates(elems):
    out = []
    txids = set()

    for elem in elems:
        if elem["hash"] in txids:
            continue

        out.append(elem)
        txids.add(elem["hash"])

    return out


def get_txs_pages_count(node, address, max_txs, per_page=TXS_LIMIT_PER_QUERY, debug=False,
                        events_types=None):
    api = FetRpcAPI(node)
    api.debug = debug
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT

    total_pages = 0
    total_txs = 0
    for event_type in events_types:
        # Number of pages/txs for events message.sender
        _, _, num_pages, num_txs = api.txs_search(address, EVENTS_TYPE_SENDER, 1, per_page)
        num_txs = min(num_txs, max_txs)
        num_pages = math.ceil(num_txs / per_page) if num_txs else 1

        logging.info("event_type: %s, num_txs: %s, num_pages: %s", event_type, num_txs, num_pages)
        total_pages += num_pages
        total_txs += num_txs

    return total_pages, total_txs
