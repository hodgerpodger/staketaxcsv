import logging
import math

from staketaxcsv.common.ibc.api_lcd_v1 import LcdAPI_v1
from staketaxcsv.settings_csv import REPORTS_DIR
from staketaxcsv.common.debug_util import debug_cache
from staketaxcsv.common.ibc.constants import (
    EVENTS_TYPE_SENDER, EVENTS_TYPE_RECIPIENT, EVENTS_TYPE_SIGNER, EVENTS_TYPE_LIST_DEFAULT)
from staketaxcsv.common.ibc.util_ibc import remove_duplicates
import time

TXS_LIMIT_PER_QUERY = 100


class LcdAPI_v2(LcdAPI_v1):
    """ >= v0.46.x (cosmos sdk version), around 2023-01 """

    @debug_cache(REPORTS_DIR)
    def _get_txs(self, wallet_address, events_type, page, limit, sleep_seconds):
        uri_path = "/cosmos/tx/v1beta1/txs"
        query_params = {
            "page": page,
            "limit": limit,
            "order_by": 2,
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

    def get_txs(self, wallet_address, events_type, page=1, limit=TXS_LIMIT_PER_QUERY, sleep_seconds=1):
        data = self._get_txs(wallet_address, events_type, page, limit, sleep_seconds)

        # No results or error
        if data.get("code") == 3:
            return [], 0, True

        if data.get("code") == 8 and "grpc: received message larger than max" in data.get("message", ""):
            logging.warning("Received grpc message too large.  "
                            "Will retry by getting one tx at a time...")
            return self._get_txs_one_by_one(wallet_address, events_type, page, limit, sleep_seconds)

        # Special case just for STARS, to get around non-deterministic bad results sometimes.
        if wallet_address.startswith("stars") and data.get("code") == 2:
            for i in range(5):
                seconds_sleep = 2**i
                logging.info("STARS: Sleeping for %s seconds ... Then retrying attempt i=%s ...", seconds_sleep, i)
                time.sleep(seconds_sleep)
                data = self._get_txs(wallet_address, events_type, page, limit, sleep_seconds)
                if data.get("code") == 2:
                    pass
                else:
                    break

        elems = data["tx_responses"]
        total_count_txs = int(data["total"])
        is_last_page = (page >= math.ceil(total_count_txs / limit))

        return elems, total_count_txs, is_last_page

    def _get_txs_one_by_one(self, wallet_address, events_type, page, limit, sleep_seconds):
        """ Rewrites original query by retrieving set of txs one-by-one. """
        p_start = (page - 1) * limit + 1
        p_end = page * limit

        elems = []
        for p in range(p_start, p_end + 1):
            logging.info("Fetching p=%s ...", p)
            data = self._get_txs(wallet_address, events_type, p, 1, sleep_seconds)
            total_count_txs = int(data["total"])
            elems.extend(data["tx_responses"])

            if p == p_end or p == total_count_txs:
                is_last_page = (p >= math.ceil(total_count_txs))
                return elems, total_count_txs, is_last_page

        return [], 0, True


def get_txs_all(node, address, max_txs, progress=None, limit=TXS_LIMIT_PER_QUERY, sleep_seconds=1,
                debug=False, stage_name="default", events_types=None):
    LcdAPI_v2.debug = debug
    api = LcdAPI_v2(node)
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT
    max_pages = math.ceil(max_txs / limit)

    out = []
    pages_total = 0
    for events_type in events_types:
        page = 1
        if progress:
            progress.report_message(f"Starting fetch for event_type={events_type}")

        for _ in range(max_pages):
            elems, _, is_last_page = api.get_txs(address, events_type, page, limit, sleep_seconds)
            out.extend(elems)

            if progress:
                pages_total += 1
                message = f"Fetched page {page} for {events_type} stage..."
                progress.report(pages_total, message, stage_name)

            page += 1

            if is_last_page:
                break

    out = remove_duplicates(out)
    return out


def get_txs_pages_count(node, address, max_txs, limit=TXS_LIMIT_PER_QUERY,
                        events_types=None, sleep_seconds=1):
    api = LcdAPI_v2(node)
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT

    total_pages = 0
    for event_type in events_types:
        # Number of queries for events message.sender
        _, num_txs, _ = api.get_txs(address, event_type, page=1, limit=limit, sleep_seconds=sleep_seconds)
        num_txs = min(num_txs, max_txs)
        num_pages = math.ceil(num_txs / limit) if num_txs else 1

        logging.info("event_type: %s, num_txs: %s, num_pages: %s", event_type, num_txs, num_pages)
        total_pages += num_pages

    return total_pages
