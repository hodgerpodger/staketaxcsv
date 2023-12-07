from staketaxcsv.algo.api.indexer import Indexer
from tests.mock_query import mock_query_two_args, mock_query_five_args
from staketaxcsv.settings_csv import TICKER_ALGO


class MockIndexer(Indexer):

    def get_transaction(self, txid):
        return mock_query_two_args(Indexer.get_transaction, self, txid, TICKER_ALGO)

    def account_exists(self, address):
        return mock_query_two_args(Indexer.account_exists, self, address, TICKER_ALGO + "/account_exists")

    def get_account(self, address):
        return mock_query_two_args(Indexer.get_account, self, address, TICKER_ALGO + "/get_account")

    def get_transactions(self, address, after_date, before_date, mynext=None):
        return mock_query_five_args(
            Indexer.get_transactions, self, address, after_date, before_date, mynext, TICKER_ALGO)

    def get_asset(self, id):
        return mock_query_two_args(Indexer.get_asset, self, id, TICKER_ALGO + "/get_asset")
