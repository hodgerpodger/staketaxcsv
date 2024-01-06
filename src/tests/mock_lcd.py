
from staketaxcsv.common.ibc.api_lcd_v1 import LcdAPI_v1
from staketaxcsv.common.ibc.api_lcd_v2 import LcdAPI_v2
from tests.mock_query import mock_query_two_args, mock_query_six_args, mock_query_three_args, mock_query_one_arg


class MockLcdAPI_v1(LcdAPI_v1):

    def _account_exists(self, wallet_address):
        return mock_query_two_args(LcdAPI_v1._account_exists, self, wallet_address, "lcdv1/_account_exists")

    def _get_txs(self, wallet_address, events_type, offset, limit, sleep_seconds):
        return mock_query_six_args(
            LcdAPI_v1._get_txs, self, wallet_address, events_type, offset, limit, sleep_seconds, "lcdv1/_get_txs")

    def balances(self, wallet_address, height=None):
        return mock_query_three_args(LcdAPI_v1.balances, self, wallet_address, height, "lcdv1/balances")

    def _ibc_address_to_denom(self, ibc_address):
        return mock_query_two_args(LcdAPI_v1._ibc_address_to_denom, self, ibc_address, "lcdv1/_ibc_address_to_denom")

    def get_tx(self, txid):
        return mock_query_two_args(LcdAPI_v1.get_tx, self, txid, "lcdv1/get_tx")

    def _node_info(self):
        return mock_query_one_arg(LcdAPI_v1._node_info, self, "lcdv1/_node_info")


class MockLcdAPI_v2(LcdAPI_v2):

    def _account_exists(self, wallet_address):
        return mock_query_two_args(LcdAPI_v1._account_exists, self, wallet_address, "lcdv2/_account_exists")

    def _get_txs(self, wallet_address, events_type, offset, limit, sleep_seconds):
        return mock_query_six_args(
            LcdAPI_v1._get_txs, self, wallet_address, events_type, offset, limit, sleep_seconds, "lcdv2/_get_txs")

    def balances(self, wallet_address, height=None):
        return mock_query_three_args(LcdAPI_v1.balances, self, wallet_address, height, "lcdv2/balances")

    def _ibc_address_to_denom(self, ibc_address):
        return mock_query_two_args(LcdAPI_v1._ibc_address_to_denom, self, ibc_address, "lcdv2/_ibc_address_to_denom")

    def get_tx(self, txid):
        return mock_query_two_args(LcdAPI_v1.get_tx, self, txid, "lcdv2/get_tx")

    def _node_info(self):
        return mock_query_one_arg(LcdAPI_v1._node_info, self, "lcdv2/_node_info")
