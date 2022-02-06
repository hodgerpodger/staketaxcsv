import logging
import urllib.parse

import requests

INDEXER_URL = "https://indexer.algoexplorerapi.io"


class IndexerAPI:

    @classmethod
    def get_transactions_by_group(cls, group_id):
        url = "{}/v2/transactions?group-id={}".format(INDEXER_URL, urllib.parse.quote(group_id))
        data, status_code = cls._query(url)

        if status_code == 200:
            return data["transactions"]
        else:
            return None

    @classmethod
    def _query(cls, url):
        logging.info("Querying Indexer url=%s...", url)
        response = requests.get(url)
        return response.json(), response.status_code
