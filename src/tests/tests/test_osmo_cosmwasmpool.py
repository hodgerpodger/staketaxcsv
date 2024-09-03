"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""
import logging
import unittest
from tests.utils_osmo import run_test, run_test_txids


class TestCosmWasmPool(unittest.TestCase):

    def test_place_limit(self):
        result = run_test(
            "osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2",
            "1C415168505E4F4C536A7960911C7EB83B94801CFB6937BE04E8D6E5ED2BA2E2"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-07-27 00:12:35  SPEND                                        0.000614000  OSMO                              1C415168505E4F4C536A7960911C7EB83B94801CFB6937BE04E8D6E5ED2BA2E2
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_cancel_limit(self):
        result = run_test(
            "osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2",
            "AFBBF3EB20E5341BF63CB52AFF3AFE923113086B598A1EB8B3513C8B6AC4A3D2"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-07-28 06:17:50  SPEND                                        0.000745000  OSMO                              AFBBF3EB20E5341BF63CB52AFF3AFE923113086B598A1EB8B3513C8B6AC4A3D2
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_place_and_cancel_limit(self):
        result = run_test_txids("osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2", [
            "006BA0CAF31B3769A580509F515626AACD7AB43819BE1F0BAD67BA9A38A2EE6B",
            "D0641B99D62F63B4033522F5F2B3B5FA0D0D83E924F15689D48D8C281E789EF9"
        ])
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-07-28 04:16:38  SPEND                                        0.000627000  OSMO                              006BA0CAF31B3769A580509F515626AACD7AB43819BE1F0BAD67BA9A38A2EE6B
2024-07-28 06:18:30  SPEND                                        0.000627000  OSMO                              D0641B99D62F63B4033522F5F2B3B5FA0D0D83E924F15689D48D8C281E789EF9
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
