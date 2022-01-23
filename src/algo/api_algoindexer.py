import logging

import requests
from settings_csv import ALGO_INDEXER_NODE

LIMIT_ALGOINDEXER = 1000


# API documentation: https://algoexplorer.io/api-dev/indexer-v2
class AlgoIndexerAPI:

    @classmethod
    def account_exists(cls, address):
        url = "{}/v2/accounts/{}".format(ALGO_INDEXER_NODE, address)
        _, status_code = cls._query(url)

        return status_code == 200

    @classmethod
    def get_transaction(cls, txhash):
        url = "{}/v2/transactions/{}".format(ALGO_INDEXER_NODE, txhash)
        data, status_code = cls._query(url)

        if status_code == 200:
            return data["transaction"]
        else:
            return None

    @classmethod
    def get_transactions(cls, address, next=None):
        url = "{}/v2/accounts/{}/transactions?limit={}".format(ALGO_INDEXER_NODE, address, LIMIT_ALGOINDEXER)
        if next:
            url += "&next={}".format(next)
        data, status_code = cls._query(url)

        if status_code == 200:
            return data["transactions"], data["next-token"] if "next-token" in data else None
        else:
            return None

    @classmethod
    def get_asset(cls, id):
        url = "{}/v2/assets/{}".format(ALGO_INDEXER_NODE, id)
        data, status_code = cls._query(url)

        if status_code == 200:
            return data["asset"]["params"]
        else:
            return None

    @classmethod
    def _query(cls, url):
        logging.info("Querying Algo Indexer url=%s...", url)
        response = requests.get(url)
        return response.json(), response.status_code
