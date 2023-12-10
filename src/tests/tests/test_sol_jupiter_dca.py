"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest
from tests.tests.test_sol import run_test


class TestSolJupiter(unittest.TestCase):

    def test_jupiter_v6_dca_swap(self):
        result = run_test(
            "9QC3q9XT3Pq81DuM2Lt7yqkCY8uZZEtiNziJgrYp6SLj",
            "S3z6oPjogs9VcYYdCugJVNe25VavQQNxp71BaeY65aSox3rrSWQs3UgGVM3Bu1FcRRGN2pcydgwUqpHfWWC4mi7"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ---------------------------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-12-10 06:07:42  TRADE    4.059345         RAY                2.777777     USDC                              S3z6oPjogs9VcYYdCugJVNe25VavQQNxp71BaeY65aSox3rrSWQs3UgGVM3Bu1FcRRGN2pcydgwUqpHfWWC4mi7
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ---------------------------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
