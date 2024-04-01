"""
For list of supported networks for mintscan api, see https://docs.cosmostation.io/apis#supported-chain-list .
"""

from urllib.parse import urlencode
import logging
import math
import pprint
import requests
import time

from staketaxcsv.common.query import get_with_retries
from staketaxcsv.settings_csv import MINTSCAN_KEY
from staketaxcsv.common.ibc.util_ibc import remove_duplicates
from staketaxcsv.common.ibc.constants import MINTSCAN_LABELS
from staketaxcsv.common.debug_util import debug_cache
from staketaxcsv.settings_csv import REPORTS_DIR
from urllib.parse import quote

TXS_LIMIT_PER_QUERY = 20


class MintscanAPI:
    """ Mintscan API for fetching transaction data """
    session = requests.Session()

    def __init__(self, ticker):
        if not MINTSCAN_KEY:
            raise Exception("Must specify STAKETAX_MINTSCAN_KEY environment variable to continue.  "
                            "For details, see https://api.mintscan.io/ and https://docs.cosmostation.io/apis")

        self.network = MINTSCAN_LABELS[ticker]
        self.base_url = "https://apis.mintscan.io/v1/" + self.network
        self.headers = {
            'Authorization': f'Bearer {MINTSCAN_KEY}',
            'Accept': 'application/json, text/plain, */*'
        }

    def _query(self, uri_path, query_params, sleep_seconds=0):
        if not MINTSCAN_KEY:
            raise Exception("Missing STAKETAX_MINTSCAN_KEY environment variable")

        url = self.base_url + uri_path
        encoded_query = "&".join(f"{quote(str(k))}={quote(str(v))}" for k, v in query_params.items())
        logging.info("Requesting url %s?%s ...", url, encoded_query)
        data = get_with_retries(self.session, url, query_params, headers=self.headers)

        if isinstance(data, dict) and data.get("statusCode") == 401:
            # message "Unauthorized"
            raise Exception(f"statusCode=401.  Unauthorized.  Your mintscan key is likely invalid or in "
                            f"pending stage.  You may need to email mintscan team for approval.  "
                            f"See https://docs.cosmostation.io/apis")

        if isinstance(data, dict) and data.get("statusCode") == 406:
            # message="LIMITED_EXCEEDED"
            # error="All allowed credits for today have been used."
            raise Exception(f"statusCode=406.  Daily api credit limit exceeded")

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

        elem = data[0]
        self._normalize_to_lcd_tx_response(elem)

        return elem

    @debug_cache(REPORTS_DIR)
    def _get_txs(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date_time=None, to_date_time=None):
        uri_path = f"/accounts/{address}/transactions"
        params = {
            'take': limit,
        }
        if search_after:
            params["searchAfter"] = search_after
        if from_date_time:
            params['fromDateTime'] = from_date_time
        if to_date_time:
            params['toDateTime'] = to_date_time

        data = self._query(uri_path, params, sleep_seconds=0.1)
        return data

    def get_txs(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date=None, to_date=None):
        """
        from_date: YYYY-MM-DD (inclusive, UTC)
        to_date: YYYY-MM-DD (inclusive, UTC)
        """
        # api truncates data to only one month if no fromDateTime.  So this is used to avoid this.
        if from_date is None:
            from_date = "2016-01-01"

        from_date_ts = from_date + " 00:00:00"
        to_date_ts = to_date + " 23:59:59" if to_date else None

        data = self._get_txs(address, search_after, limit, from_date_ts, to_date_ts)
        transactions = data.get("transactions", [])
        next_search_after = data.get("pagination", {}).get("searchAfter")
        total_txs = data.get("pagination", {}).get("totalCount")
        is_last_page = next_search_after is None

        for transaction in transactions:
            self._normalize_to_lcd_tx_response(transaction)

        return transactions, next_search_after, is_last_page, total_txs

    def _normalize_to_lcd_tx_response(self, elem):
        """ Change structure to LCD tx_response field, due to processors being based on this. """
        self._restructure(elem["tx"])

    def _restructure(self, x):
        if isinstance(x, dict):
            self._restructure_dict_with_type_field(x)
            for k, v in x.items():
                self._restructure(v)

        if isinstance(x, list):
            for a in x:
                self._restructure(a)

    def _restructure_dict_with_type_field(self, x):
        if "type" in x:
            tx_type = x["type"]
            if tx_type in x:
                value = x[tx_type]
                x.update(value)
                del x[tx_type]
        elif "@type" in x:
            tx_type = x["@type"]
            field_tx_type = tx_type.replace(".", "-")  # i.e. "/cosmos.tx.v1beta1.Tx" -> "/cosmos-tx-v1beta1-Tx"
            if field_tx_type in x:
                value = x[field_tx_type]
                x.update(value)
                del x[field_tx_type]

    @debug_cache(REPORTS_DIR)
    def _get_balances(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date_time=None, to_date_time=None):
        uri_path = f"/accounts/{address}/balances"
        params = {
            'take': limit,
        }
        if search_after:
            params["searchAfter"] = search_after
        if from_date_time:
            params['fromDateTime'] = from_date_time
        if to_date_time:
            params['toDateTime'] = to_date_time

        data = self._query(uri_path, params, sleep_seconds=0.1)
        return data

    def get_balances(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date=None, to_date=None):
        """
        from_date: YYYY-MM-DD (inclusive, UTC)
        to_date: YYYY-MM-DD (inclusive, UTC)
        """
        # api truncates data to only one month if no fromDateTime.  So this is used to avoid this.
        if from_date is None:
            from_date = "2016-01-01"

        from_date_ts = from_date + " 00:00:00"
        to_date_ts = to_date + " 23:59:59" if to_date else None

        data = self._get_balances(address, search_after, limit, from_date_ts, to_date_ts)

        balances = data.get("balances", [])
        next_search_after = data.get("pagination", {}).get("searchAfter")
        is_last_page = next_search_after is None

        return balances, next_search_after, is_last_page


def get_txs_page_count(ticker, address, max_txs, start_date=None, end_date=None):
    _, _, _, total_txs = MintscanAPI(ticker).get_txs(address, from_date=start_date, to_date=end_date)
    num_txs = min(total_txs, max_txs)

    # "1 +" is because extra page that retries zero transactions
    num_pages = 1 + math.ceil(num_txs / TXS_LIMIT_PER_QUERY) if num_txs else 1

    return num_pages


def get_txs_all(ticker, address, max_txs, progress=None, start_date=None, end_date=None):
    api = MintscanAPI(ticker)
    max_pages = math.ceil(max_txs / TXS_LIMIT_PER_QUERY)

    out = []
    search_after = None

    if progress:
        progress.report_message(f"Starting fetch stage ...")
    for i in range(max_pages):
        elems, search_after, is_last_page, _ = api.get_txs(
            address, search_after, limit=TXS_LIMIT_PER_QUERY, from_date=start_date, to_date=end_date)
        out.extend(elems)

        if progress:
            progress.report(i + 1, f"Fetched page {i + 1} ...")

        if is_last_page:
            break

    out = remove_duplicates(out)
    return out


def get_balances_all(ticker, address, max_txs, start_date=None, end_date=None):
    api = MintscanAPI(ticker)
    max_pages = math.ceil(max_txs / TXS_LIMIT_PER_QUERY)

    out = []
    search_after = None

    for i in range(max_pages):
        balances, search_after, is_last_page = api.get_balances(
            address, search_after, limit=TXS_LIMIT_PER_QUERY, from_date=start_date, to_date=end_date)
        out.extend(balances)

        if is_last_page:
            break

    out.sort(key=lambda b: b["timestamp"], reverse=True)

    return out


def main():
    logging.basicConfig(level=logging.INFO)

    # Example usage
    ticker = "JUNO"
    address = "juno1wl4nc3ysp8gft5ewkyf97ue547xjgu8jjh93la"
    max_txs = 1000  # Maximum number of transactions to fetch
    transactions = get_txs_all(ticker, address, max_txs)

    page_count = get_txs_page_count(ticker, address, 20000)

    api = MintscanAPI(ticker)
    transaction = api.get_tx("E4CA3E5C86313DAFE7CD726A3AACC4BA6E96956CF2B50B68BE3CF2F261AD28DD")

    print("len is ")
    print(len(transactions))

    print("transactions are ")
    pprint.pprint([t["txhash"] for t in transactions])

    print("page_count is")
    print(page_count)

    print("transactions timestamps are")
    pprint.pprint([t["timestamp"] for t in transactions])

    print("transaction timestamp is ")
    pprint.pprint(transaction["timestamp"])

    balances = get_balances_all(ticker, address, max_txs)

    print("balance timestamps are ")
    pprint.pprint([b["timestamp"] for b in balances])


if __name__ == "__main__":
    main()
