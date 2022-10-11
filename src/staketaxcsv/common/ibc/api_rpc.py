import ast
import base64
import functools
import logging
import math
import time
from urllib.parse import urlencode

import requests
from dateutil import parser
from staketaxcsv.common.ibc.api_common import (
    EVENTS_TYPE_LIST_DEFAULT,
    EVENTS_TYPE_RECIPIENT,
    EVENTS_TYPE_SENDER,
    EVENTS_TYPE_SIGNER,
    remove_duplicates,
)
from staketaxcsv.common.ibc.protobuf_decoder import (
    CosmosTransactionFeeExtractor,
    ProtobufParser,
    ProtobufParserCallback,
)
from staketaxcsv.fet.fetchhub1.api_rpc import TXS_LIMIT_PER_QUERY


class RpcAPI:
    session = requests.Session()
    debug = False

    def __init__(self, node):
        self.node = node

    def _query(self, uri_path, query_params, sleep_seconds=0.0):
        url = f"{self.node}{uri_path}"
        logging.info("Requesting url %s?%s ...", url, urlencode(query_params))
        response = self.session.get(url, params=query_params)

        if sleep_seconds:
            time.sleep(sleep_seconds)
        return response.json()

    def _block(self, height):
        uri_path = "/block"
        query_params = {"height": height}

        data = self._query(uri_path, query_params, sleep_seconds=0.2)

        return data

    def _txs_search(self, wallet_address, events_type, page, per_page):
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

    def get_tx(self, txid):
        uri_path = "/tx"
        query_params = {
            "hash": "0x" + txid
        }
        data = self._query(uri_path, query_params, sleep_seconds=1)
        return data.get("result", None)

    def txs_search(self, wallet_address, events_type, page, per_page):
        data = self._txs_search(wallet_address, events_type, page, per_page)

        elems = data["result"]["txs"]
        total_count_txs = int(data["result"]["total_count"])
        total_count_pages = math.ceil(total_count_txs / per_page)
        if page >= total_count_pages:
            next_page = None
        else:
            next_page = page + 1

        return elems, next_page, total_count_pages, total_count_txs

    @functools.lru_cache
    def block_time(self, height):
        data = self._block(height)

        return data["result"]["block"]["header"]["time"]


def get_txs_all(node, wallet_address, progress, max_txs, limit=TXS_LIMIT_PER_QUERY, debug=False,
                stage_name="default", events_types=None):
    api = RpcAPI(node)
    api.debug = debug
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT
    max_pages = math.ceil(max_txs / limit)

    out = []
    page_for_progress = 1
    for events_type in events_types:
        for page in range(1, max_pages + 1):
            message = f"Fetching page {page_for_progress} ..."
            progress.report(page_for_progress, message, stage_name)
            page_for_progress += 1

            elems, next_page, _, _ = api.txs_search(wallet_address, events_type, page, limit)

            out.extend(elems)
            if next_page is None:
                break

    out = remove_duplicates(out, tx_hash_key="hash", timestamp_sort=False)
    return out


def get_txs_pages_count(node, address, max_txs, limit=TXS_LIMIT_PER_QUERY, debug=False,
                        events_types=None):
    api = RpcAPI(node)
    api.debug = debug
    events_types = events_types if events_types else EVENTS_TYPE_LIST_DEFAULT

    total_pages = 0
    for event_type in events_types:
        _, _, num_pages, num_txs = api.txs_search(address, event_type, 1, limit)
        num_txs = min(num_txs, max_txs)
        num_pages = math.ceil(num_txs / limit) if num_txs else 1

        logging.info("event_type: %s, num_txs: %s, num_pages: %s", event_type, num_txs, num_pages)
        total_pages += num_pages

    return total_pages


def normalize_rpc_txns(node, elems):
    """
    Normalize the RPC transaction element to have fields a LCD transaction element
    would have.
    Decodes base64 encoded fields as needed.
    """
    for elem in elems:
        elem = _decode(elem)

        # add the txhash field
        elem["txhash"] = elem["hash"]

        # add the timestamp field
        _add_timestamp_from_block_time(elem, node)

        # add the fee
        _add_fee_from_cosmos_transaction_authinfo(elem)

        # add transaction messages
        _add_messages_from_logs(elem)


def _decode(elem):
    """ Modifies transaction data with decoded version """
    elem["tx_result"]["log"] = ast.literal_eval(elem["tx_result"]["log"])

    events = elem["tx_result"]["events"]
    for event in events:
        for kv in event["attributes"]:
            k, v = kv["key"], kv["value"]

            kv["key"] = base64.b64decode(k).decode()
            kv["value"] = base64.b64decode(v).decode()

    elem["tx"] = base64.b64decode(elem["tx"])

    return elem


def _add_timestamp_from_block_time(elem, node):
    """
    Add a timestamp field to an RPC element.
    """
    # since there isn't a timestamp on the RPC transaction data, we
    # need to get the timestamp based on the block processing time
    # it's also converted from the RPC format to the LCD format:
    #     i.e. "2021-08-26T21:08:44.86954814Z" -> "2021-08-26T21:08:44Z"
    height = elem["height"]
    block_timestamp = RpcAPI(node).block_time(height)
    block_timestamp = parser.parse(block_timestamp).strftime("%Y-%m-%dT%H:%M:%SZ")
    elem["timestamp"] = block_timestamp


def _add_fee_from_cosmos_transaction_authinfo(elem):
    """
    Extracts the fee denom and amount from the protobuf encoded cosmos transaction data and
    adds it to the RPC element.
    """
    fee_extractor_callback = CosmosTransactionFeeExtractor()
    protobuf_parser = ProtobufParser(elem["tx"], fee_extractor_callback)
    protobuf_parser.parse()

    elem["tx"] = {
        "auth_info": {
            "fee": {
                "amount": [
                    {
                        "denom": fee_extractor_callback.fee_denom,
                        "amount": fee_extractor_callback.fee_amount
                    }
                ]
            }
        }
    }


def _add_messages_from_logs(elem):

    messages = []

    logs = elem["tx_result"]["log"]
    elem["logs"] = logs
    for log in logs:
        for event in log["events"]:
            event_type = event["type"]
            event_attributes = event["attributes"]

            if event_type != "message":
                continue

            message = _make_message_from_event_attributes(event_attributes)
            messages.append(message)

    # add messages into the transaction body element
    elem["tx"]["body"] = {
        "messages": messages
    }


def _make_message_from_event_attributes(event_attributes):
    message = {}
    for kv in event_attributes:
        key, value = kv["key"], kv["value"]
        message[key] = value

    # set the message type field that LCD responses provide
    #
    # note: we do not do any other combination of events to produce application
    # specific message fields and rely on transfer events to dictate any movement of coins
    message["@type"] = message["action"]
    del message["action"]

    return message
