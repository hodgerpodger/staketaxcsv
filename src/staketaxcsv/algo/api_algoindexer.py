import datetime
from itertools import cycle
import logging
import math
from random import sample
from requests import Session
from requests.adapters import HTTPAdapter, Retry

from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.common.debug_util import use_debug_files
from staketaxcsv.settings_csv import ALGO_ALT_INDEXER_NODE, ALGO_HIST_INDEXER_NODE, ALGO_INDEXER_NODE, REPORTS_DIR

# https://developer.algorand.org/docs/get-details/indexer/#paginated-results
ALGOINDEXER_LIMIT = 2000

ALGOINDEXER_NODES = [
    ALGO_INDEXER_NODE,
    ALGO_ALT_INDEXER_NODE
]


# API documentation: https://algoexplorer.io/api-dev/indexer-v2
class AlgoIndexerAPI:
    session = None

    def __init__(self):
        if not AlgoIndexerAPI.session:
            AlgoIndexerAPI.session = Session()
            retries = Retry(total=5, backoff_factor=5)
            AlgoIndexerAPI.session.mount("https://", HTTPAdapter(max_retries=retries))

        self._nodes = cycle(sample(ALGOINDEXER_NODES, len(ALGOINDEXER_NODES)))
        self._txns_node = None

    def _select_node(self):
        return next(self._nodes)

    def account_exists(self, address):
        endpoint = f"v2/accounts/{address}/transactions"
        params = {"limit": 1}

        _, status_code = self._query(self._select_node(), endpoint, params)

        return status_code == 200

    @use_debug_files(localconfig, REPORTS_DIR)
    def get_account(self, address):
        endpoint = f"v2/accounts/{address}"
        params = {"include-all": True}

        data, status_code = self._query(ALGO_HIST_INDEXER_NODE, endpoint, params)

        if status_code == 599:
            data, status_code = self._query(self._select_node(), endpoint, params)

        if status_code == 200:
            return data["account"]
        else:
            return None

    def get_transaction(self, txhash):
        endpoint = f"v2/transactions/{txhash}"

        data, status_code = self._query(self._select_node(), endpoint)

        if status_code == 200:
            return data["transaction"]
        else:
            return None

    def get_transactions(self, address, after_date=None, before_date=None, min_round=None, next=None):
        endpoint = f"v2/accounts/{address}/transactions"
        params = {"limit": ALGOINDEXER_LIMIT}
        if after_date:
            params["after-time"] = after_date.isoformat()
        if before_date:
            params["before-time"] = before_date.isoformat()
        if min_round:
            params["min-round"] = min_round
        if next:
            params["next"] = next

        # next-token is server specific so can't change node in the middle of multi-page requests
        if next is None:
            self._txns_node = self._select_node()

        data, status_code = self._query(self._txns_node, endpoint, params)

        if status_code == 200:
            return data["transactions"], data.get("next-token")
        else:
            return [], None

    @use_debug_files(localconfig, REPORTS_DIR)
    def get_all_transactions(self, address):
        next = None
        out = []

        max_txs = localconfig.limit
        max_queries = math.ceil(max_txs / ALGOINDEXER_LIMIT)
        logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)

        after_date = None
        before_date = None
        if localconfig.start_date:
            after_date = datetime.date.fromisoformat(localconfig.start_date)
        if localconfig.end_date:
            before_date = datetime.date.fromisoformat(localconfig.end_date) + datetime.timedelta(days=1)

        for _ in range(max_queries):
            transactions, next = self.get_transactions(
                address, after_date, before_date, localconfig.min_round, next)
            out.extend(transactions)

            if not next:
                break

        return out

    def get_transactions_by_group(self, group_id):
        endpoint = "v2/transactions"
        params = {"group-id": group_id}

        data, status_code = self._query(ALGO_HIST_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["transactions"]
        else:
            return []

    def get_asset(self, id):
        endpoint = f"v2/assets/{id}"

        data, status_code = self._query(self._select_node(), endpoint)

        if status_code == 599:
            data, status_code = self._query(self._select_node(), endpoint)

        if status_code == 200:
            return data["asset"]["params"]
        else:
            return None

    def _query(self, node_url, endpoint, params=None):
        url = f"{node_url}/{endpoint}"

        logging.info("Querying Algo Indexer %s...", url)

        try:
            response = AlgoIndexerAPI.session.get(url, params=params, timeout=5)
        except Exception as e:
            logging.error("Exception when querying '%s', exception=%s", url, str(e))
        else:
            return response.json(), response.status_code

        return {}, 599
