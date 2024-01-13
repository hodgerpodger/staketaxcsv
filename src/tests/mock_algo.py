from staketaxcsv.algo.api.indexer import Indexer
from tests.mock_query import mock_query_two_args, mock_query_five_args
from staketaxcsv.settings_csv import TICKER_ALGO
DIRNAME = TICKER_ALGO


class MockIndexer(Indexer):

    def get_transaction(self, txid):
        return mock_query_two_args(Indexer.get_transaction, self, txid, DIRNAME + "/get_transaction")

    def account_exists(self, address):
        return mock_query_two_args(Indexer.account_exists, self, address, DIRNAME + "/account_exists")

    def get_account(self, address):
        return mock_query_two_args(Indexer.get_account, self, address, DIRNAME + "/get_account")

    def get_transactions(self, address, after_date, before_date, mynext=None):
        return mock_query_five_args(
            Indexer.get_transactions, self, address, after_date, before_date, mynext, DIRNAME + "/get_transactions")

    def get_asset(self, id):
        return mock_query_two_args(Indexer.get_asset, self, id, DIRNAME + "/get_asset")
