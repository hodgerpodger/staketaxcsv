import logging
import urllib.parse

import requests
from common.Singleton import Singleton
from settings_csv import ALGO_HIST_INDEXER_NODE, ALGO_INDEXER_NODE

LIMIT_ALGOINDEXER = 1000


# API documentation: https://algoexplorer.io/api-dev/indexer-v2
class AlgoIndexerAPI(metaclass=Singleton):
    def __init__(self):
        self._session = requests.Session()

    def account_exists(self, address):
        url = "{}/v2/accounts/{}/transactions?limit={}".format(ALGO_INDEXER_NODE, address, 1)
        _, status_code = self._query(url)

        return status_code == 200

    def get_transaction(self, txhash):
        url = "{}/v2/transactions/{}".format(ALGO_INDEXER_NODE, txhash)
        data, status_code = self._query(url)

        if status_code == 200:
            return data["transaction"]
        else:
            return None

    def get_transactions(self, address, after_date=None, before_date=None, next=None):
        url = "{}/v2/accounts/{}/transactions?limit={}".format(ALGO_INDEXER_NODE, address, LIMIT_ALGOINDEXER)
        if after_date:
            url += "&after-time={}".format(after_date.isoformat())
        if before_date:
            url += "&before-time={}".format(before_date.isoformat())
        if next:
            url += "&next={}".format(next)
        data, status_code = self._query(url)

        if status_code == 200:
            return data["transactions"], data["next-token"] if "next-token" in data else None
        else:
            return None

    def get_transactions_by_group(self, group_id):
        url = "{}/v2/transactions?group-id={}".format(ALGO_HIST_INDEXER_NODE, urllib.parse.quote(group_id))
        data, status_code = self._query(url)

        if status_code == 200:
            return data["transactions"]
        else:
            return None

    def get_asset(self, id):
        url = "{}/v2/assets/{}".format(ALGO_INDEXER_NODE, id)
        data, status_code = self._query(url)

        if status_code == 200:
            return data["asset"]["params"]
        else:
            return None

    def _query(self, url):
        logging.info("Querying Algo Indexer url=%s...", url)
        response = self._session.get(url)
        return response.json(), response.status_code
