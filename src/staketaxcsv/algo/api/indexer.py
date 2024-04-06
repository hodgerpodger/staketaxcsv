import datetime
import logging
import math
import os
import time
from typing import Optional, Tuple
from requests import Session
from requests.adapters import HTTPAdapter, Retry

from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.common.debug_util import debug_cache
from staketaxcsv.settings_csv import ALGO_INDEXER_NODE, REPORTS_DIR

# https://developer.algorand.org/docs/get-details/indexer/#paginated-results
INDEXER_LIMIT = 2000


# API documentation: https://editor.swagger.io/?url=https://openapi.algonode.cloud/indexer2.oas3.json
class Indexer:
    session = None

    def __init__(self):
        if not Indexer.session:
            Indexer.session = Session()
            retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
            Indexer.session.mount("https://", HTTPAdapter(max_retries=retries))

    def account_exists(self, address):
        endpoint = f"v2/accounts/{address}/transactions"
        params = {"limit": 1}

        _, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        return status_code == 200

    @debug_cache(os.path.join(REPORTS_DIR, "algo", "accounts"))
    def get_account(self, address: str) -> Optional[dict]:
        """
        This function retrieves account information for a given address.

        Args:
          address (str): The address of the Algorand account that we want to retrieve information for.

        Returns:
          A dictionary containing information about the account if successful, `None` otherwise.
          See account schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Account
        """
        endpoint = f"v2/accounts/{address}"
        params = {"include-all": True}

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["account"]
        else:
            return None

    def get_transaction(self, txid: str) -> Optional[dict]:
        """
        This function retrieves a transaction with a given ID.

        Args:
          txid (str): The ID of the transaction ID that is being requested.

        Returns:
          A dictionary containing information about a transaction if successful, `None` otherwise.
          See transaction schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Transaction
        """
        endpoint = f"v2/transactions/{txid}"

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint)

        if status_code == 200:
            return data["transaction"]
        else:
            return None

    def get_transactions(self,
                         address: str,
                         after_date: Optional[datetime.date] = None,
                         before_date: Optional[datetime.date] = None,
                         min_round: Optional[int] = None,
                         next: Optional[str] = None) -> Tuple[list, Optional[str]]:
        """
        This function retrieves transactions for a given address with optional filters and pagination.

        Args:
          address (str): The Algorand address for which to retrieve transactions.
          after_date (Optional[datetime.date]): Include results after the given date.
          before_date (Optional[datetime.date]): Include results before the given date.
          min_round (Optional[int]): The minimum round number for transactions to be included in the
        results. Transactions with a round number lower than this value will be excluded.
          next (Optional[str]): An optional string that represents a token used to
        retrieve the next page of results in a multi-page request. It is returned in the response of the
        previous request and can be passed as a parameter to this function to retrieve the next page of
        transactions.

        Returns:
          a tuple containing a list of transactions and an optional string representing the next token for
        pagination. See transaction schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Transaction
        """
        endpoint = f"v2/accounts/{address}/transactions"
        params = {"limit": INDEXER_LIMIT}
        if after_date:
            params["after-time"] = after_date.isoformat()
        if before_date:
            params["before-time"] = before_date.isoformat()
        if min_round:
            params["min-round"] = min_round
        if next:
            params["next"] = next

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["transactions"], data.get("next-token")
        else:
            return [], None

    @debug_cache(os.path.join(REPORTS_DIR, "algo", "transactions"))
    def get_all_transactions(self, address: str) -> list:
        """
        This function retrieves all transactions for a given address within a specified date range and
        minimum round, using a maximum number of queries and transactions per query. The transactions are
        obtained by making multiple queries to the indexer API, with a maximum number of transactions per
        query determined by the `localconfig.limit` parameter.

        Returns:
            list: List of transaction objects that match the specified criteria,
                see schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Transaction
        """
        next = None
        out = []

        max_txs = localconfig.limit
        max_queries = math.ceil(max_txs / INDEXER_LIMIT)
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

    def get_transactions_by_group(self, group_id: str) -> list[dict]:
        """
        This function retrieves a list of transactions associated with a specific group ID.

        Args:
          group_id (str): The group ID. More details on transaction groups\
          at https://developer.algorand.org/docs/get-details/atomic_transfers/

        Returns:
          This function returns a list of dictionaries containing transaction data for a specific group ID.
        """
        endpoint = "v2/transactions"
        params = {"group-id": group_id}

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["transactions"]
        else:
            return []

    @debug_cache(os.path.join(REPORTS_DIR, "algo", "transactions"))
    def get_transactions_by_app(self, app_id: int, round: int, address: Optional[str] = None) -> list[dict]:
        """
        This function retrieves a list of transactions for a specific application ID, round, and optional
        address.

        Args:
          app_id (int): The ID of the application for which transactions are being requested.
          round (int): The round number of the transactions to retrieve.
          address (Optional[str]): Optional parameter to filter transactions by a specific address.

        Returns:
          This function returns a list of dictionaries containing transactions made with the specified parameters.
        """
        endpoint = "v2/transactions"
        params = {
            "limit": INDEXER_LIMIT,
            "application-id": app_id,
            "round": round
        }
        if address:
            params["address"] = address

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["transactions"]
        else:
            return []

    @debug_cache(os.path.join(REPORTS_DIR, "algo", "assets"))
    def get_asset(self, id: int) -> Optional[dict]:
        """
        This function retrieves asset information.

        Args:
          id (int): Algorand Standard Asset (ASA) id.

        Returns:
          A dictionary containing asset details if successful, `None` otherwise.
          See asset params schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Asset
        """
        endpoint = f"v2/assets/{id}"
        params = {"include-all": True}

        # Temporarily slow down asset requests until we either cache them
        # or https://github.com/algorand/go-algorand/issues/5250 is resolved.
        time.sleep(0.1)

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        if status_code == 200:
            return data["asset"]
        else:
            return None

    @debug_cache(os.path.join(REPORTS_DIR, "algo", "assets"))
    def get_deleted_asset(self, id: int) -> Optional[dict]:
        """
        This function retrieves information for an asset that has been deleted.

        Args:
          id (int): Algorand Standard Asset (ASA) id.

        Returns:
          A dictionary containing asset details if successful, `None` otherwise.
          See asset params schema at https://app.swaggerhub.com/apis/algonode/indexer/2.0#/Asset
        """
        endpoint = f"v2/assets/{id}/transactions"
        params = {"tx-type": "acfg"}

        data, status_code = self._query(ALGO_INDEXER_NODE, endpoint, params)

        if status_code == 200 and len(data.get("transactions", [])) > 0:
            return data["transactions"][0]["asset-config-transaction"]
        else:
            return None

    def _query(self, node_url, endpoint, params=None):
        url = f"{node_url}/{endpoint}"

        logging.info("Querying Algo Indexer %s with params %s...", url, params)

        try:
            response = Indexer.session.get(url, params=params, timeout=5)
        except Exception as e:
            logging.error("Exception when querying '%s', exception=%s", url, str(e))
        else:
            return response.json(), response.status_code

        return {}, 599
