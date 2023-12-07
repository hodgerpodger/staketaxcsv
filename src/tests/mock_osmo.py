from tests.mock_query import mock_query_one_arg
from staketaxcsv.settings_csv import TICKER_OSMO
from staketaxcsv.osmo.api_data import get_tx as my_get_tx


def mock_get_tx(txid):
    return mock_query_one_arg(my_get_tx, txid, TICKER_OSMO)
