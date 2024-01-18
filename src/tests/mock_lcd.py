
from staketaxcsv.common.ibc.api_lcd_v1 import LcdAPI_v1
from staketaxcsv.common.ibc.api_lcd_v2 import LcdAPI_v2
from tests.mock_query import mock_query_two_args, mock_query_six_args, mock_query_three_args, mock_query_one_arg
LCDV1 = "lcdv1"
LCDV2 = "lcdv2"


class MockLcdAPI_v1(LcdAPI_v1):

    def _account_exists(self, wallet_address):
        return mock_query_two_args(LcdAPI_v1._account_exists, self, wallet_address, LCDV1 + "/_account_exists")

    def _get_txs(self, wallet_address, events_type, offset, limit, sleep_seconds):
        return mock_query_six_args(
            LcdAPI_v1._get_txs, self, wallet_address, events_type, offset, limit, sleep_seconds, LCDV1 + "/_get_txs")

    def balances(self, wallet_address, height=None):
        return mock_query_three_args(LcdAPI_v1.balances, self, wallet_address, height, LCDV1 + "/balances")

    def _ibc_address_to_denom(self, ibc_address):
        return mock_query_two_args(LcdAPI_v1._ibc_address_to_denom, self, ibc_address, LCDV1 + "/_ibc_address_to_denom")

    def get_tx(self, txid):
        return mock_query_two_args(LcdAPI_v1.get_tx, self, txid, LCDV1 + "/get_tx")

    def _node_info(self):
        return mock_query_one_arg(LcdAPI_v1._node_info, self, LCDV1 + "/_node_info")

    def _staking_params(self):
        return mock_query_one_arg(LcdAPI_v1._staking_params, self, LCDV1 + "/_staking_params")



class MockLcdAPI_v2(LcdAPI_v2):

    def _account_exists(self, wallet_address):
        return mock_query_two_args(LcdAPI_v1._account_exists, self, wallet_address, LCDV2 + "/_account_exists")

    def _get_txs(self, wallet_address, events_type, offset, limit, sleep_seconds):
        return mock_query_six_args(
            LcdAPI_v1._get_txs, self, wallet_address, events_type, offset, limit, sleep_seconds, LCDV2 + "/_get_txs")

    def balances(self, wallet_address, height=None):
        return mock_query_three_args(LcdAPI_v1.balances, self, wallet_address, height, LCDV2 + "/balances")

    def _ibc_address_to_denom(self, ibc_address):
        return mock_query_two_args(LcdAPI_v1._ibc_address_to_denom, self, ibc_address, LCDV2 + "/_ibc_address_to_denom")

    def get_tx(self, txid):
        return mock_query_two_args(LcdAPI_v1.get_tx, self, txid, LCDV2 + "/get_tx")

    def _node_info(self):
        return mock_query_one_arg(LcdAPI_v1._node_info, self, LCDV2 + "/_node_info")
