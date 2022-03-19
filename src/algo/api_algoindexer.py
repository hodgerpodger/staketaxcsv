import logging
import urllib.parse

import requests
from settings_csv import ALGO_HIST_INDEXER_NODE, ALGO_INDEXER_NODE

LIMIT_ALGOINDEXER = 1000


# API documentation: https://algoexplorer.io/api-dev/indexer-v2
class AlgoIndexerAPI:
    session = requests.Session()

    def account_exists(self, address):
        endpoint = f"v2/accounts/{address}/transactions"
        params = {"limit": 1}

        _, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        return status_code == 200

    def get_account(self, address):
        endpoint = f"v2/accounts/{address}"
        params = {"include-all": True}

        data, status_code = self._query(ALGO_HIST_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["account"]
        else:
            return None

    def get_transaction(self, txhash):
        endpoint = f"v2/transactions/{txhash}"

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint)

        if status_code == 200:
            return data["transaction"]
        else:
            return None

    def get_transactions(self, address, after_date=None, before_date=None, next=None):
        endpoint = f"v2/accounts/{address}/transactions"
        params = {"limit": LIMIT_ALGOINDEXER}
        if after_date:
            params["after-time"] = after_date.isoformat()
        if before_date:
            params["before-time"] = before_date.isoformat()
        if next:
            params["next"] = next

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["transactions"], data.get("next-token")
        else:
            return [], None

    def get_transactions_by_group(self, group_id):
        endpoint = "v2/transactions"
        params = {"group-id": urllib.parse.quote(group_id)}

        data, status_code = self._query(ALGO_HIST_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["transactions"]
        else:
            return None

    def get_asset(self, id):
        endpoint = f"v2/assets/{id}"

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint)

        if status_code == 200:
            return data["asset"]["params"]
        else:
            return None

    def _query(self, base_url, endpoint, params=None):
        logging.info("Querying Algo Indexer endpoint %s...", endpoint)
        url = f"{base_url}/{endpoint}"
        response = self.session.get(url, params=params)
        return response.json(), response.status_code
