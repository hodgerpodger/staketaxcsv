import hashlib
import json
from staketaxcsv.sol.api_rpc import RpcAPI
from tests.mock_query import mock_query_one_arg, mock_query_two_args, mock_query_three_args
from staketaxcsv.settings_csv import TICKER_SOL


class MockRpcAPI(RpcAPI):

    @classmethod
    def _fetch_staking_addresses(cls, wallet_address):
        return mock_query_one_arg(
            RpcAPI._fetch_staking_addresses, wallet_address, TICKER_SOL + "/_fetch_staking_address")

    @classmethod
    def fetch_tx(cls, txid):
        return mock_query_one_arg(RpcAPI.fetch_tx, txid, TICKER_SOL + "/fetch_tx")

    @classmethod
    def _get_inflation_reward(cls, staking_address, epoch):
        return mock_query_two_args(
            RpcAPI._get_inflation_reward, staking_address, epoch, TICKER_SOL + "/_get_inflation_reward")

    @classmethod
    def _get_txids(cls, wallet_address, limit=None, before=None):
        return mock_query_three_args(
            RpcAPI._get_txids, wallet_address, limit, before, TICKER_SOL + "/_get_txids")

    @classmethod
    def _fetch_token_accounts(cls, wallet_address, program_id):
        return mock_query_two_args(
            RpcAPI._fetch_token_accounts, wallet_address, program_id, TICKER_SOL + "/_fetch_token_accounts")

    @classmethod
    def fetch_account(cls, wallet_address):
        return mock_query_one_arg(
            RpcAPI.fetch_account, wallet_address, TICKER_SOL + "/fetch_account")

    @classmethod
    def get_block_time(cls, block):
        return mock_query_one_arg(RpcAPI.get_block_time, block, TICKER_SOL + "/get_block_time")
