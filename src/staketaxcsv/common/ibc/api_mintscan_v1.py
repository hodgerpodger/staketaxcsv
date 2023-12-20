"""
Experimental class.  Not integrated yet into reports.

"""

import logging
import math
import pprint
import requests
from staketaxcsv.settings_csv import MINTSCAN_KEY
TXS_LIMIT_PER_QUERY = 20


class MintscanAPI:
    """ Mintscan API for fetching transaction data """

    def __init__(self, network):
        self.base_url = "https://apis.mintscan.io/v1"
        self.network = network
        self.headers = {
            'Authorization': f'Bearer {MINTSCAN_KEY}',
            'Accept': 'application/json, text/plain, */*'
        }

    def _get_txs(self, address, search_after, limit, from_date=None, to_date=None):
        uri_path = f"/{self.network}/accounts/{address}/transactions"
        params = {
            'take': limit,
            'searchAfter': search_after,
        }
        if from_date:
            params['fromDateTime'] = from_date
        if to_date:
            params['toDateTime'] = to_date

        response = requests.get(self.base_url + uri_path, headers=self.headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data: {response.text}")
        logging.info("Fetched response from %s", response.url)
        return response.json()

    def get_txs(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date=None, to_date=None):
        # api truncates data to only one month if no fromDateTime.  So this is used to avoid this.
        if from_date is None:
            from_date = "2020-01-01"

        data = self._get_txs(address, search_after, limit, from_date, to_date)
        transactions = data.get("transactions", [])
        next_search_after = data.get("pagination", {}).get("searchAfter")
        is_last_page = next_search_after is None

        return transactions, next_search_after, is_last_page


def get_txs_all(network, address, max_txs, from_date=None, to_date=None):
    api = MintscanAPI(network)
    max_pages = math.ceil(max_txs / TXS_LIMIT_PER_QUERY)

    out = []
    search_after = None

    for i in range(max_pages):
        logging.info("Fetching page %i for address=%s using search_after=%s, from_date=%s, to_date=%s",
                     i, address, search_after, from_date, to_date)
        elems, search_after, is_last_page = api.get_txs(
            address, search_after, limit=TXS_LIMIT_PER_QUERY, from_date=from_date, to_date=to_date)
        logging.info("Got %s transactions in result", len(elems))

        out.extend(elems)

        if is_last_page:
            break

    out = _remove_duplicates(out)
    return out


def _remove_duplicates(transactions):
    """
    Remove duplicate transactions from the list.
    Assumes each transaction has a unique 'txhash'.
    """
    seen = set()
    unique_transactions = []
    for transaction in transactions:
        txhash = transaction.get('txhash')
        if txhash not in seen:
            seen.add(txhash)
            unique_transactions.append(transaction)
    return unique_transactions


def main():
    logging.basicConfig(level=logging.INFO)

    # Example usage
    network = "juno"
    address = "juno1wl4nc3ysp8gft5ewkyf97ue547xjgu8jjh93la"
    max_txs = 1000  # Maximum number of transactions to fetch
    transactions = get_txs_all(network, address, max_txs)

    print("len is ")
    print(len(transactions))

    print("transactions are ")
    pprint.pprint([t["txhash"] for t in transactions])

    print("transaction timestamps are")
    pprint.pprint([t["timestamp"] for t in transactions])


if __name__ == "__main__":
    main()
