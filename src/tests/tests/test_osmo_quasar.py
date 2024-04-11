"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from tests.utils_osmo import run_test


class TestOsmoQuasar(unittest.TestCase):

    def test_quasar_claim_rewards(self):
        result = run_test(
            "osmo1hw4c4f7005mv8jgguztztwu9f8e5qyutr7v2ar",
            "22BD4955CAD2020AEF2DF753EA70448E2334ABCA3E6C14DF25979523043DDA1E"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  -----------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee          fee_currency  txid
2024-04-03 06:21:44  STAKING  1.060789         SOMM                                           0.000744000  OSMO          22BD4955CAD2020AEF2DF753EA70448E2334ABCA3E6C14DF25979523043DDA1E-0
2024-04-03 06:21:44  STAKING  0.000047751      WETH                                           0.000744000  OSMO          22BD4955CAD2020AEF2DF753EA70448E2334ABCA3E6C14DF25979523043DDA1E-0
2024-04-03 06:21:44  STAKING  0.000061725      YIELDETH                                       0.000744000  OSMO          22BD4955CAD2020AEF2DF753EA70448E2334ABCA3E6C14DF25979523043DDA1E-0
-------------------  -------  ---------------  -----------------  -----------  -------------  -----------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
