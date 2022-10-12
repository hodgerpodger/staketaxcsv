import logging

import requests
from staketaxcsv.common.Singleton import Singleton
from staketaxcsv.settings_csv import COVALENT_API_KEY, COVALENT_NODE


# Documentation: https://www.covalenthq.com/docs/developer/
class CovalentAPI(metaclass=Singleton):
    def __init__(self, chain_id):
        if not COVALENT_API_KEY:
            raise TypeError("Empty API_KEY")

        self._session = requests.Session()
        self._session.auth = ('', COVALENT_API_KEY)
        self._chain_id = chain_id

    def get_transactions(self, address, block_signed_at_asc=False, no_logs=False,
            page_number=None, page_size=None):
        """
        Retrieve all transactions for address including their decoded log events.
        This endpoint does a deep-crawl of the blockchain to retrieve all kinds
        of transactions that references the address.

        :param str address: Passing in an ENS resolves automatically.
        :param bool block_signed_at_asc: Sort the transactions in chronological
            ascending order. By default it's set to false and returns transactions
            in chronological descending order.
        :param bool no_logs: Setting this to true will omit decoded event logs,
            resulting in lighter and faster responses. By default it's set to false.
        :param int page_number: The specific page to be returned.
        :param int page_size: The number of results per page.
        """
        endpoint = f"v1/{self._chain_id}/address/{address}/transactions_v2"
        params = {
            "block-signed-at-asc": block_signed_at_asc,
            "no-logs": no_logs,
            "page-number": page_number,
            "page-size": page_size,
        }

        data, status_code = self._query(endpoint, params)

        if status_code == 200:
            data_obj = data.get("data", {})
            has_more = (data_obj["pagination"].get("has_more", False)
                if "pagination" in data_obj and data_obj["pagination"] else False)
            return data_obj.get("items", []), has_more
        else:
            return None

    def get_transaction(self, txhash, no_logs=False):
        """
        Retrieve the transaction data with their decoded event logs.

        :param str txhash: Transaction hash.
        :param bool no_logs: Setting this to true will omit decoded event logs,
            resulting in lighter and faster responses. By default it's set to false.
        """
        endpoint = f"v1/{self._chain_id}/transaction_v2/{txhash}"
        params = {
            "no-logs": no_logs,
        }

        data, status_code = self._query(endpoint, params)

        if status_code == 200:
            return data.get("data", {}).get("items", [])
        else:
            return None

    def _query(self, endpoint, params=None):
        url = f"{COVALENT_NODE}/{endpoint}"
        logging.info("Querying Covalent endpoint %s...", url)
        response = self._session.get(url, params=params)
        response_json = response.json()
        if not response.ok:
            logging.error("Error querying Covalent endpoint %s: %s",
                url, response_json.get("error_message", "unknown"))
        return response_json, response.status_code
