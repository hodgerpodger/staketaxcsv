"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from tests.utils_osmo import run_test


class TestOsmoMars(unittest.TestCase):

    def test_mars_claim_rewards(self):
        result = run_test(
            "osmo1ha94fyhagrk5wphdn27qp96l20lfgzsrqdhqfk",
            "D5F8634C5E6E2F974D6E5C11514972D361ACE6BBCFC3BA043DD11F6A50B9A5A3"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-04-01 21:50:47  STAKING  0.000002000      MARS                                           0.003609  OSMO          D5F8634C5E6E2F974D6E5C11514972D361ACE6BBCFC3BA043DD11F6A50B9A5A3-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
