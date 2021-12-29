import logging
import requests
import time

from urllib.parse import urlunparse, urlencode

OSMO_API_SCHEME = "https"
OSMO_API_NETLOC = "api-osmosis-chain.imperator.co"
OSMO_GET_TX_COUNT_PATH_TEMPLATE = "/txs/v1/tx/count/{address}"
OSMO_GET_TXS_PATH_TEMPLATE = "/txs/v1/tx/address/{address}"
LIMIT = 50


class OsmoDataAPI:

    @classmethod
    def get_count_txs(cls, address):
        uri_path = OSMO_GET_TX_COUNT_PATH_TEMPLATE.format(address=address)
        data = cls._query(uri_path)
        return sum(row["count"] for row in data)

    @classmethod
    def get_txs(cls, address, offset=None):
        uri_path = OSMO_GET_TXS_PATH_TEMPLATE.format(address=address)
        query_params = {}
        query_params["limit"] = LIMIT
        if offset:
            query_params["offset"] = offset
        data = cls._query(uri_path, query_params)

        # Extract "tx_response" (found to be common data across multiple APIs)
        return [row["tx_response"] for row in data]

    @classmethod
    def _query(cls, uri_path, query_params={}):
        url = urlunparse((
            OSMO_API_SCHEME, 
            OSMO_API_NETLOC, 
            uri_path, 
            None, 
            urlencode(query_params), 
            None,
        ))
        logging.info("Querying url=%s...", url)
        response = requests.get(url)
        time.sleep(1)
        return response.json()
