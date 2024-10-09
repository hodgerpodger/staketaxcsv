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


class TestOsmoMarsCreditManager(unittest.TestCase):

    def test_borrow_withdraw(self):
        result = run_test(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-03-11 08:43:28  SPEND                                         0.000012000  OSMO           0.009397  OSMO          9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE-0
2024-03-11 08:43:28  BORROW    1.258961         AKT                                                                    9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE-1
2024-03-11 08:43:28  TRANSFER  1.258961         AKT                                                                    9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE-1
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_withdraw_account_balance(self):
        result = run_test(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "4F24719C4887D7AC5E6185F16AFC4BEC55B97675EE9679B0BA432DC6CA054CE6"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-04-07 09:06:53  SPEND                                         0.000012000  OSMO           0.016232  OSMO          4F24719C4887D7AC5E6185F16AFC4BEC55B97675EE9679B0BA432DC6CA054CE6-0
2024-04-07 09:06:53  TRANSFER  0.383886         TIA                                                                    4F24719C4887D7AC5E6185F16AFC4BEC55B97675EE9679B0BA432DC6CA054CE6-1
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_repay_from_wallet(self):
        result = run_test(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "07A90D52C7C9131E2135BCD5081FD086B949E9540287B43E30A6D8BBFB8AB573"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-10-02 17:00:33  SPEND                                        0.000016000  OSMO           0.004335  OSMO          07A90D52C7C9131E2135BCD5081FD086B949E9540287B43E30A6D8BBFB8AB573-0
2024-10-02 17:00:33  REPAY                                        1.79         OSMO                                   07A90D52C7C9131E2135BCD5081FD086B949E9540287B43E30A6D8BBFB8AB573-1
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
