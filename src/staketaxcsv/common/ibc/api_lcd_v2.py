import logging
import math

from staketaxcsv.common.ibc.api_lcd_v1 import LcdAPI_v1
from staketaxcsv.settings_csv import REPORTS_DIR
from staketaxcsv.common.debug_util import use_debug_files
from staketaxcsv.common.ibc.api_common import (
    EVENTS_TYPE_LIST_DEFAULT,
    EVENTS_TYPE_RECIPIENT,
    EVENTS_TYPE_SENDER,
    EVENTS_TYPE_SIGNER,
    remove_duplicates,
)

TXS_LIMIT_PER_QUERY = 100


class LcdAPI_v2(LcdAPI_v1):
    """ >= v0.46.x (cosmos sdk version), around 2023-01 """

    @use_debug_files(None, REPORTS_DIR)
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

        elems = data["tx_responses"]
        total_count_txs = int(data["total"])
        is_last_page = (page >= math.ceil(total_count_txs / limit))

        return elems, total_count_txs, is_last_page


def get_txs_all(node, wallet_address, progress, max_txs, limit=TXS_LIMIT_PER_QUERY, sleep_seconds=1,
                debug=False, stage_name="default", events_types=None):
    LcdAPI_v2.debug = debug
    api = LcdAPI_v2(node)
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT
    max_pages = math.ceil(max_txs / limit)

    out = []

    for events_type in events_types:
        page = 1

        for _ in range(0, max_pages):
            message = f"Fetching page {page} for {events_type} ..."
            progress.report(page, message, stage_name)

            elems, _, is_last_page = api.get_txs(wallet_address, events_type, page, limit, sleep_seconds)
            out.extend(elems)

            page += 1
            if is_last_page:
                break

    out = remove_duplicates(out)
    return out


def get_txs_pages_count(node, address, max_txs, limit=TXS_LIMIT_PER_QUERY, debug=False,
                        events_types=None, sleep_seconds=1):
    LcdAPI_v2.debug = debug
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
