
from staketaxcsv.common.ibc.api_mintscan_v1 import MintscanAPI, TXS_LIMIT_PER_QUERY
from tests.mock_query import mock_query_two_args, mock_query_six_args


class MockMintscanAPI(MintscanAPI):

    def __init__(self, ticker):
        self.ticker = ticker
        super().__init__(ticker)

    def _dir(self, dirname):
        return "mintscan/" + self.ticker + "/" + dirname

    def _get_tx(self, txid):
        return mock_query_two_args(MintscanAPI._get_tx, self, txid, self._dir("_get_tx"))

    def _get_txs(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date_time=None, to_date_time=None):
        return mock_query_six_args(MintscanAPI._get_txs, self, address, search_after, limit,
                                   from_date_time, to_date_time, self._dir("_get_txs"))

    def _get_balances(self, address, search_after=None, limit=TXS_LIMIT_PER_QUERY, from_date_time=None, to_date_time=None):
        return mock_query_six_args(MintscanAPI._get_balances, self, address, search_after, limit,
                                   from_date_time, to_date_time, self._dir("_get_balances"))
