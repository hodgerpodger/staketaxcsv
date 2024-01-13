from tests.mock_query import mock_query_one_arg
from staketaxcsv.settings_csv import TICKER_OSMO
from staketaxcsv.osmo.api_data import get_tx as my_get_tx
from staketaxcsv.osmo.api_osmosis import get_symbol as my_get_symbol
from staketaxcsv.osmo.api_osmosis import get_exponent as my_get_exponent
DIRNAME = TICKER_OSMO


def mock_get_tx(txid):
    return mock_query_one_arg(my_get_tx, txid, DIRNAME)


def mock_get_symbol(ibc_address):
    return mock_query_one_arg(my_get_symbol, ibc_address, DIRNAME)


def mock_get_exponent(currency):
    return mock_query_one_arg(my_get_exponent, currency, DIRNAME)
