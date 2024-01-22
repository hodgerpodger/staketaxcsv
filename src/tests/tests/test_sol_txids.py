"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from unittest.mock import patch
import staketaxcsv.report_sol
from tests.mock_sol import MockRpcAPI
from staketaxcsv.sol.txids import get_txids_for_accounts
WALLET_ADDRESS = "4kLALtynrmd6pU2LkGXZCmUaMDfsnVixs7SkLjPKNJQG"
TXIDS_FOR_WALLET = [
    '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',
]


def mock_fetch_token_accounts(wallet_address):

    return MockRpcAPI.fetch_token_accounts(wallet_address)


@patch("staketaxcsv.sol.txids.RpcAPI", new=MockRpcAPI)
class TestSolTxids(unittest.TestCase):

    @patch("staketaxcsv.report_sol.RpcAPI.fetch_token_accounts", new=mock_fetch_token_accounts)
    def test_txids_returns_transactions_for_all_addresses(self):
        pass

    def test_txids_with_old_txs_no_timestamp(self):
        txids = get_txids_for_accounts([WALLET_ADDRESS], None, None)
        self.assertEqual(txids, TXIDS_FOR_WALLET)

    @patch("staketaxcsv.sol.txids.LIMIT_PER_QUERY", 5)
    def test_txids_low_limit_per_query(self):
        txids = get_txids_for_accounts([WALLET_ADDRESS], None, None)
        self.assertEqual(txids, TXIDS_FOR_WALLET)

    @patch("staketaxcsv.sol.txids.LIMIT_PER_QUERY", 5)
    def test_txids_start_date_only(self):
        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2021-02-09")
        self.assertEqual(txids, TXIDS_FOR_WALLET[4:])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2021-02-10")
        self.assertEqual(txids, TXIDS_FOR_WALLET[6:])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2025-02-10")
        self.assertEqual(txids, [])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2023-11-29")
        self.assertEqual(txids, TXIDS_FOR_WALLET[23:])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2001-11-29")
        self.assertEqual(txids, TXIDS_FOR_WALLET)

    @patch("staketaxcsv.sol.txids.LIMIT_PER_QUERY", 5)
    def test_txids_end_date_only(self):
        txids = get_txids_for_accounts([WALLET_ADDRESS], None, end_date="2021-02-09")
        self.assertEqual(txids, TXIDS_FOR_WALLET[:6])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, end_date="2021-02-10")
        self.assertEqual(txids, TXIDS_FOR_WALLET[:8])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, end_date="2025-02-10")
        self.assertEqual(txids, TXIDS_FOR_WALLET)

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, end_date="2000-11-29")
        self.assertEqual(txids, [])

    @patch("staketaxcsv.sol.txids.LIMIT_PER_QUERY", 5)
    def test_txids_start_date_end_date(self):
        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2001-01-01", end_date="2030-01-01")
        self.assertEqual(txids, TXIDS_FOR_WALLET)

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2021-02-09", end_date="2021-02-09")
        self.assertEqual(txids, TXIDS_FOR_WALLET[4:6])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2021-02-08", end_date="2021-02-08")
        self.assertEqual(txids, [])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2001-01-08", end_date="2021-02-08")
        self.assertEqual(txids, TXIDS_FOR_WALLET[:4])

        txids = get_txids_for_accounts([WALLET_ADDRESS], None, start_date="2001-01-08", end_date="2021-02-09")
        self.assertEqual(txids, TXIDS_FOR_WALLET[:6])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
