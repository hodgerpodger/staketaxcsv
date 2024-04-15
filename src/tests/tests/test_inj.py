"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest

from staketaxcsv.inj.handle_deposit_claim import Deposits
from tests.utils_inj import run_test_txids, run_test


class TestInj(unittest.TestCase):

    def setUp(self):
        Deposits.txs = {}

    def test_self_transfer(self):
        result = run_test(
            "inj137aqf3usphm78scte2pnt5z02hvcqpyafkhzsj",
            "1A8245481AC4E67FDA01485918B10A201367DB988144FC2B7DECA839B1360A9F"
        )
        correct_result = """
-------------------  --------------  ---------------  -----------------  -----------  -------------  -----------  ------------  ------------------------------------------------------------------
timestamp            tx_type         received_amount  received_currency  sent_amount  sent_currency  fee          fee_currency  txid
2023-12-11 19:13:59  _SELF_TRANSFER                                                                  0.000103445  INJ           1A8245481AC4E67FDA01485918B10A201367DB988144FC2B7DECA839B1360A9F-0
-------------------  --------------  ---------------  -----------------  -----------  -------------  -----------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_deposit_claim(self):
        result = run_test(
            "inj1mner97yu4ns6ds2fd9es7k8n9jh3yxs3jkzh86",
            "E13E8719CF49E5D190F632BFF383010CF76B093558CD8F6BF4886C7211922D35"
        )
        correct_result = """
-------------------  --------  ------------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount     received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2021-12-11 15:49:15  TRANSFER  100104.79000000001  INJ                                                               E13E8719CF49E5D190F632BFF383010CF76B093558CD8F6BF4886C7211922D35-0
-------------------  --------  ------------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_duplicate_deposit_claim(self):
        result = run_test_txids(
            "inj1mner97yu4ns6ds2fd9es7k8n9jh3yxs3jkzh86",
            [
                "E13E8719CF49E5D190F632BFF383010CF76B093558CD8F6BF4886C7211922D35",
                "B5D77457B78184E8C77AB0D92DED3B374ED516ACCA0827C1140E87A8FB0CE77D",
                "16D3104F4CFD25D8C6D761E61F5320802FD64F3D3DA9A9671FF68A817697A993"
            ]
        )
        correct_result = """
-------------------  ------------------------  ------------------  -----------------  -----------  -------------  -----------  ------------  ------------------------------------------------------------------
timestamp            tx_type                   received_amount     received_currency  sent_amount  sent_currency  fee          fee_currency  txid
2021-12-11 15:49:15  TRANSFER                  100104.79000000001  INJ                                                                       E13E8719CF49E5D190F632BFF383010CF76B093558CD8F6BF4886C7211922D35-0
2021-12-11 15:49:17  _DUPLICATE_DEPOSIT_CLAIM                                                                     0.000063202  INJ           B5D77457B78184E8C77AB0D92DED3B374ED516ACCA0827C1140E87A8FB0CE77D-0
2021-12-11 15:49:25  _DUPLICATE_DEPOSIT_CLAIM                                                                     0.000066305  INJ           16D3104F4CFD25D8C6D761E61F5320802FD64F3D3DA9A9671FF68A817697A993-0
-------------------  ------------------------  ------------------  -----------------  -----------  -------------  -----------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_send_to_eth(self):
        result = run_test(
            "inj1mner97yu4ns6ds2fd9es7k8n9jh3yxs3jkzh86",
            "9295E239680531D7734A97B7AB3F190A5DFA8A5E7074AEF450DAAC7363257D76"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  ------------------  -------------  ------------------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount         sent_currency  fee                 fee_currency  txid
2022-03-20 05:42:58  TRANSFER                                      7266.7749815498155  INJ            1.8452184501845017  INJ           9295E239680531D7734A97B7AB3F190A5DFA8A5E7074AEF450DAAC7363257D76-0
-------------------  --------  ---------------  -----------------  ------------------  -------------  ------------------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
