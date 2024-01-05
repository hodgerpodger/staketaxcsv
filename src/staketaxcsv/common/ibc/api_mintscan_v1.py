"""
Experimental class.  Not integrated yet into reports.

"""

from urllib.parse import urlencode
import logging
import math
import pprint
import requests
import time

from staketaxcsv.common.query import get_with_retries
from staketaxcsv.settings_csv import MINTSCAN_KEY
from staketaxcsv.common.ibc.api_common import remove_duplicates

TXS_LIMIT_PER_QUERY = 20

# ticker -> mintscan api network name (https://docs.cosmostation.io/apis#supported-chain-list)
MINTSCAN_API_CHAINS = {
    "AKT": "akash",
    "ARCH": "archway",
    "ATOM": "cosmos",
    "TIA": "celestia",
    "DYDX": "dydx",
    "EVMOS": "evmos",
    "INJ": "injective",
    "JUNO": "juno",
    "KAVA": "kava",
    "NTRN": "neutron",
    "OSMO": "osmosis",
    "STRD": "stride",
}

class MintscanAPI:
    """ Mintscan API for fetching transaction data """
    session = requests.Session()

    def __init__(self, ticker):
        self.network = MINTSCAN_API_CHAINS[ticker]
        self.base_url = "https://apis.mintscan.io/v1/" + self.network
        self.headers = {
            'Authorization': f'Bearer {MINTSCAN_KEY}',
            'Accept': 'application/json, text/plain, */*'
        }

    def _query(self, uri_path, query_params, sleep_seconds=0):
        if not MINTSCAN_KEY:
            raise Exception("Missing MINTSCAN_KEY")

        url = self.base_url + uri_path
        logging.info("Requesting url %s?%s ...", url, urlencode(query_params))
        data = get_with_retries(self.session, url, query_params, headers=self.headers)

        if sleep_seconds:
            time.sleep(sleep_seconds)
        return data

    def _get_tx(self, txid):
        uri_path = f"/txs/{txid}"
        params = {}
        data = self._query(uri_path, params)
        return data

    def get_tx(self, txid):
        data = self._get_tx(txid)
        return data[0]

    def _get_txs(self, address, search_after, limit, from_date=None, to_date=None):
        uri_path = f"/accounts/{address}/transactions"
        params = {
            'take': limit,
            'searchAfter': search_after,
        }
        if from_date:
            params['fromDateTime'] = from_date
        if to_date:
            params['toDateTime'] = to_date

        data = self._query(uri_path, params, sleep_seconds=0.1)
        return data

    def get_txs(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date=None, to_date=None):
        # api truncates data to only one month if no fromDateTime.  So this is used to avoid this.
        if from_date is None:
            from_date = "2020-01-01"

        data = self._get_txs(address, search_after, limit, from_date, to_date)
        transactions = data.get("transactions", [])
        next_search_after = data.get("pagination", {}).get("searchAfter")
        is_last_page = next_search_after is None

        return transactions, next_search_after, is_last_page


def get_txs_all(ticker, address, max_txs, progress=None, from_date=None, to_date=None):
    api = MintscanAPI(ticker)
    max_pages = math.ceil(max_txs / TXS_LIMIT_PER_QUERY)

    out = []
    search_after = None

    progress.report_message(f"Starting fetch stage ...")
    for i in range(max_pages):
        logging.info("Fetching mintscan page %i for address=%s using search_after=%s, from_date=%s, to_date=%s",
                     i+1, address, search_after, from_date, to_date)

        elems, search_after, is_last_page = api.get_txs(
            address, search_after, limit=TXS_LIMIT_PER_QUERY, from_date=from_date, to_date=to_date)
        out.extend(elems)

        if progress:
            message = f"Fetched page {i+1} ..."
            progress.report(i+1, message)

        if is_last_page:
            break

    out = remove_duplicates(out)
    return out


def main():
    logging.basicConfig(level=logging.INFO)

    # Example usaget
    ticker = "JUNO"
    address = "juno1wl4nc3ysp8gft5ewkyf97ue547xjgu8jjh93la"
    max_txs = 1000  # Maximum number of transactions to fetch
    transactions = get_txs_all(ticker, address, max_txs)
    api = MintscanAPI(ticker)
    transaction = api.get_tx("E4CA3E5C86313DAFE7CD726A3AACC4BA6E96956CF2B50B68BE3CF2F261AD28DD")

    print("len is ")
    print(len(transactions))

    print("transactions are ")
    pprint.pprint([t["txhash"] for t in transactions])

    print("transactions timestamps are")
    pprint.pprint([t["timestamp"] for t in transactions])

    print("transaction timestamp is ")
    pprint.pprint(transaction["timestamp"])


if __name__ == "__main__":
    main()
