"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from tests.utils_osmo import run_test


class TestTfm(unittest.TestCase):

    def test_execute_swap_operations(self):
        result = run_test(
            "osmo1phxc2wg9pcvc9wsqhckmajrgn4qhl7fjuqqm58",
            "008E5D21AE63A031E7F677E777FA33FF31BDDC294318F5EEE6FC31F9308E2CC1"
        )
        correct_result = """
-------------------  -------  ------------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount     received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-08-20 07:24:22  TRADE    2.8365639545736663  INJ                54.04659     USDC.axl       0.007188  OSMO          008E5D21AE63A031E7F677E777FA33FF31BDDC294318F5EEE6FC31F9308E2CC1-0
-------------------  -------  ------------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
