"""
Experimental class.  Not integrated yet into reports.

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

TXS_LIMIT_PER_QUERY = 20


class MintscanAPI:
    """ Mintscan API for fetching transaction data """
    session = requests.Session()

    def __init__(self, ticker):
        self.network = MINTSCAN_LABELS[ticker]
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
        self._restructure_dict_with_type_field(elem["tx"])

        if "body" in elem["tx"] and "messages" in elem["tx"]["body"]:
            messages = elem["tx"]["body"]["messages"]
            for message in messages:
                self._restructure_dict_with_type_field(message)

                if "msgs" in message:
                    msgs = message["msgs"]
                    for msg in msgs:
                        self._restructure_dict_with_type_field(msg)

        if "value" in elem["tx"] and "msg" in elem["tx"]["value"]:
            msg = elem["tx"]["value"]["msg"]
            for m in msg:
                self._restructure_dict_with_type_field(m)

    def _restructure_dict_with_type_field(self, x):
        if "type" in x:
            tx_type = x["type"]
            value = x[tx_type]
            x.update(value)
            del x[tx_type]
        elif "@type" in x:
            tx_type = x["@type"]
            field_tx_type = tx_type.replace(".", "-")  # i.e. "/cosmos.tx.v1beta1.Tx" -> "/cosmos-tx-v1beta1-Tx"
            value = x[field_tx_type]
            x.update(value)
            del x[field_tx_type]


def get_txs_page_count(ticker, address, max_txs, start_date=None, end_date=None):
    _, _, _, total_txs = MintscanAPI(ticker).get_txs(address, from_date=start_date, to_date=end_date)
    num_txs = min(total_txs, max_txs)
    num_pages = math.ceil(num_txs / TXS_LIMIT_PER_QUERY) if num_txs else 1
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


if __name__ == "__main__":
    main()
