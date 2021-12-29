import logging
import requests
import time

from typing import Any
from urllib.parse import urlunparse, urlencode, quote

OSMO_API_SCHEME = "https"

OSMO_HISTORICAL_API_NETLOC = "api-osmosis.imperator.co"
OSMO_GET_SYMBOL_PATH = "/search/v1/symbol"

OSMO_DATA_API_NETLOC = "api-osmosis-chain.imperator.co"
OSMO_GET_TX_COUNT_PATH_TEMPLATE = "/txs/v1/tx/count/{address}"
OSMO_GET_TXS_PATH_TEMPLATE = "/txs/v1/tx/address/{address}"

OSMO_TX_API_NETLOC = "api-osmosis.cosmostation.io"
OSMO_GET_TX_PATH_TEMPLATE = "/v1/tx/hash/{txid}"

LIMIT = 50


def _query(scheme: str, netloc: str, uri_path: str, query_params: dict[str, Any] = {}) -> dict[str, Any]:
    url = urlunparse((
        scheme,
        netloc,
        uri_path,
        None,
        urlencode(query_params),
        None,
    ))
    logging.info("Querying url=%s...", url)
    response = requests.get(url)
    time.sleep(1)
    return response.json()


def get_count_txs(address: str) -> int:
    uri_path = OSMO_GET_TX_COUNT_PATH_TEMPLATE.format(address=address)

    data = _query(OSMO_API_SCHEME, OSMO_DATA_API_NETLOC, uri_path)
    return sum(row["count"] for row in data)


def get_txs(address: str, offset: int = None) -> list[dict[str, Any]]:
    uri_path = OSMO_GET_TXS_PATH_TEMPLATE.format(address=address)
    query_params = {}
    query_params["limit"] = LIMIT
    if offset:
        query_params["offset"] = offset

    data = _query(OSMO_API_SCHEME, OSMO_DATA_API_NETLOC, uri_path, query_params)
    # Extract "tx_response" (found to be common data across multiple APIs)
    return [row["tx_response"] for row in data]


def get_symbol(ibc_address: str) -> str or None:
    query_params = {"denom": quote(ibc_address)}

    data = _query(OSMO_API_SCHEME, OSMO_HISTORICAL_API_NETLOC, OSMO_GET_SYMBOL_PATH, query_params)
    return data["symbol"] if "symbol" in data else None


def get_tx(txid: str) -> Any:
    query_params = {"txid": txid}
    uri_path = OSMO_GET_TX_PATH_TEMPLATE.format(txid=txid)

    data = _query(OSMO_API_SCHEME, OSMO_TX_API_NETLOC, uri_path, query_params)
    return data["data"]
