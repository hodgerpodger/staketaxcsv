
import json
import logging
import math
import os
import requests
import time
from urllib.parse import urlencode
from settings_csv import REPORTS_DIR


class RpcAPI:
    session = requests.Session()

    def __init__(self, node):
        self.node = node
        self.debug = False

    def _query(self, uri_path, query_params, sleep_seconds=0):
        url = f"{self.node}{uri_path}"
        logging.info("Requesting url %s?%s ...", url, urlencode(query_params))
        response = self.session.get(url, params=query_params)

        if sleep_seconds:
            time.sleep(sleep_seconds)
        return response.json()

    def get_tx(self, txid):
        uri_path = "/tx"
        query_params = {
            "hash": "0x" + txid
        }
        data = self._query(uri_path, query_params, sleep_seconds=1)
        return data.get("tx_response", None)
