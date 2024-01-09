"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from unittest.mock import patch

from tests.settings_test import specialtest, mintscan_api
from staketaxcsv.settings_csv import TICKER_ATOM
from staketaxcsv.common.ibc.api_mintscan_v1 import MintscanAPI, TXS_LIMIT_PER_QUERY, get_txs_page_count

ADDRESS = "cosmos1qqp2aydslhpx4emvqdhsyn8ztrltd4zezcr22h"


@specialtest
@mintscan_api
class TestMintscan(unittest.TestCase):

    def test_get_tx(self):
        txid = "2348F12174EB5AAB27A919598CA8881E5DCD8F192D631AB7BAA414973BCC28C5"

        api = MintscanAPI(TICKER_ATOM)
        elem = api.get_tx(txid)

        self.assertEqual(elem["timestamp"], "2024-01-04T21:10:01Z")

    def test_get_txs_with_dates(self):
        api = MintscanAPI(TICKER_ATOM)

        # get transactions between 2022-03-03 to 2022-03-05 (inclusive, UTC)
        elems, next_search_after, is_last_page, total_txs = api.get_txs(
            ADDRESS, from_date="2022-03-03", to_date="2022-03-05")
        timestamps = [elem["timestamp"] for elem in elems]

        self.assertEqual(timestamps, [
            '2022-03-05T13:46:15Z',
            '2022-03-05T13:44:19Z',
            '2022-03-04T10:07:22Z',
            '2022-03-04T09:57:48Z',
        ])
        self.assertTrue(next_search_after is not None)
        self.assertEqual(is_last_page, False)
        self.assertEqual(total_txs, 4)

        # try subsequent query, which should return 0 trnasactions
        elems, next_search_after, is_last_page, total_txs = api.get_txs(
            ADDRESS, search_after=next_search_after, from_date="2022-03-03", to_date="2022-03-05")

        self.assertEqual(elems, [])
        self.assertEqual(next_search_after, None)
        self.assertEqual(is_last_page, True)
        self.assertEqual(total_txs, 4)

    def test_get_txs_no_dates(self):
        api = MintscanAPI(TICKER_ATOM)

        # get transactions between 2022-03-03 to 2022-03-05 (inclusive, UTC)
        elems, next_search_after, is_last_page, total_txs = api.get_txs(
            ADDRESS, from_date=None, to_date=None)
        timestamps = [elem["timestamp"] for elem in elems]

        year_of_first_timestamp = int(timestamps[0].split("-")[0])
        self.assertGreaterEqual(year_of_first_timestamp, 2024)
        self.assertEqual(len(timestamps), TXS_LIMIT_PER_QUERY)
        self.assertTrue(next_search_after is not None)
        self.assertEqual(is_last_page, False)
        self.assertGreater(total_txs, 184)

    def test_txs_page_count(self):
        num_pages = get_txs_page_count(TICKER_ATOM, ADDRESS, 20000, None, None)
        self.assertGreaterEqual(num_pages, 10)

        num_pages = get_txs_page_count(TICKER_ATOM, ADDRESS, 20000, start_date="2022-03-03", end_date="2022-03-05")
        self.assertEqual(num_pages, 2)
