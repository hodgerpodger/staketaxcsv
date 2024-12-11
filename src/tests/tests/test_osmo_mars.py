"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from tests.utils_osmo import run_test, run_test_verbose


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
-------------------  --------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
timestamp            tx_type         received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-03-11 08:43:28  SPEND                                               0.000012000  OSMO           0.009397  OSMO          9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE-0
2024-03-11 08:43:28  BORROW          1.258961         AKT                                                                    9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE-1-0
2024-03-11 08:43:28  _MARS_WITHDRAW                                                                                          9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE-1-1
-------------------  --------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

        result = run_test_verbose(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "9E9145D8F4057F8A35578001398AD47F20E767C50EE91C45BCD6BAA141E141FE",
        )
        self.assertTrue("withdraw 1.258961 AKT" in result)

    def test_withdraw_account_balance(self):
        result = run_test(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "4F24719C4887D7AC5E6185F16AFC4BEC55B97675EE9679B0BA432DC6CA054CE6"
        )
        correct_result = """
-------------------  --------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
timestamp            tx_type         received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-04-07 09:06:53  SPEND                                               0.000012000  OSMO           0.016232  OSMO          4F24719C4887D7AC5E6185F16AFC4BEC55B97675EE9679B0BA432DC6CA054CE6-0
2024-04-07 09:06:53  _MARS_WITHDRAW                                                                                          4F24719C4887D7AC5E6185F16AFC4BEC55B97675EE9679B0BA432DC6CA054CE6-1-0
-------------------  --------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

        result = run_test_verbose(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "4F24719C4887D7AC5E6185F16AFC4BEC55B97675EE9679B0BA432DC6CA054CE6",
        )
        self.assertTrue("withdraw 0.383886 TIA" in result)

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

    def test_lend_deposit_amount_exact(self):
        result = run_test(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "7B6BB8354765417E7442A98A6E494D98FAC87EAEBAB2F2A7C599906590245497"
        )
        correct_result = """
-------------------  -------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
timestamp            tx_type        received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-10-03 16:46:52  SPEND                                              0.000016000  OSMO           0.019735  OSMO          7B6BB8354765417E7442A98A6E494D98FAC87EAEBAB2F2A7C599906590245497-0
2024-10-03 16:46:52  _MARS_DEPOSIT                                                                                          7B6BB8354765417E7442A98A6E494D98FAC87EAEBAB2F2A7C599906590245497-1-0
2024-10-03 16:46:52  _MARS_LEND                                                                                             7B6BB8354765417E7442A98A6E494D98FAC87EAEBAB2F2A7C599906590245497-1-1
-------------------  -------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

        result = run_test_verbose(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "7B6BB8354765417E7442A98A6E494D98FAC87EAEBAB2F2A7C599906590245497",
        )
        self.assertTrue("deposit 12.824204 USDC" in result)
        self.assertTrue("lend 12.824204 USDC" in result)

    def test_lend_deposit_amount_account_balance(self):
        result = run_test(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "38A12E02E164D8534B8EBCAC8B15D2651E5EE553320EFD3025730DCD090B98DE"
        )
        correct_result = """
-------------------  ----------  ---------------  -----------------  -----------  -------------  ------  ------------  --------------------------------------------------------------------
timestamp            tx_type     received_amount  received_currency  sent_amount  sent_currency  fee     fee_currency  txid
2024-07-10 20:12:33  SPEND                                           0.000016000  OSMO           0.0215  OSMO          38A12E02E164D8534B8EBCAC8B15D2651E5EE553320EFD3025730DCD090B98DE-0
2024-07-10 20:12:33  _MARS_LEND                                                                                        38A12E02E164D8534B8EBCAC8B15D2651E5EE553320EFD3025730DCD090B98DE-1-0
-------------------  ----------  ---------------  -----------------  -----------  -------------  ------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

        result = run_test_verbose(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "38A12E02E164D8534B8EBCAC8B15D2651E5EE553320EFD3025730DCD090B98DE",
        )
        self.assertTrue("lend 28.532982 USDT" in result)

    def test_lend_deposit_no_first_message(self):
        result = run_test(
            "osmo1kwmk8mfrna308nm0jftrgravuuwuuk3fvmwma8",
            "73B6822DDA4BCA3DE397B429F9F4F8E809DBB6C115DA4967A74C721CA2141983"
        )
        correct_result = """
-------------------  -------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
timestamp            tx_type        received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-09-24 17:08:28  _MARS_DEPOSIT                                                                  0.005136  OSMO          73B6822DDA4BCA3DE397B429F9F4F8E809DBB6C115DA4967A74C721CA2141983-0-0
2024-09-24 17:08:28  _MARS_LEND                                                                                             73B6822DDA4BCA3DE397B429F9F4F8E809DBB6C115DA4967A74C721CA2141983-0-1
-------------------  -------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

        result = run_test_verbose(
            "osmo1kwmk8mfrna308nm0jftrgravuuwuuk3fvmwma8",
            "73B6822DDA4BCA3DE397B429F9F4F8E809DBB6C115DA4967A74C721CA2141983",
        )
        self.assertTrue("deposit 241.688373 USDC" in result)
        self.assertTrue("lend 241.688373 USDC" in result)

    def test_reclaim_withdraw(self):
        result = run_test(
            "osmo1kwmk8mfrna308nm0jftrgravuuwuuk3fvmwma8",
            "C7637097E8E4D977E383F697619881311BD91BA313D04C6E895D6C946E49122D"
        )
        correct_result = """
-------------------  --------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
timestamp            tx_type         received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-09-25 01:49:49  _MARS_RECLAIM                                                                   0.014024  OSMO          C7637097E8E4D977E383F697619881311BD91BA313D04C6E895D6C946E49122D-0-0
2024-09-25 01:49:49  _MARS_WITHDRAW                                                                                          C7637097E8E4D977E383F697619881311BD91BA313D04C6E895D6C946E49122D-0-1
-------------------  --------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

        result = run_test_verbose(
            "osmo1kwmk8mfrna308nm0jftrgravuuwuuk3fvmwma8",
            "C7637097E8E4D977E383F697619881311BD91BA313D04C6E895D6C946E49122D",
        )
        self.assertTrue("reclaim 100.0 USDC" in result)
        self.assertTrue("withdraw 100.0 USDC" in result)

    def test_create_credit_account_no_spend_fee(self):
        result = run_test(
            "osmo1kpz70lr2402qt8d3f5zgdq4smslap83w6l2axd",
            "664945C59DEF14E81A3249FBF21170AB8A9DEB386CD9CAADA395A10DEB3FB453"
        )
        correct_result = """
-------------------  ---------------------------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type                      received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-02-18 14:54:00  SPEND                                                            0.000012000  OSMO           0.002519  OSMO          664945C59DEF14E81A3249FBF21170AB8A9DEB386CD9CAADA395A10DEB3FB453-0
2024-02-18 14:54:00  _MARS_CREATE_CREDIT_ACCOUNT                                                                                          664945C59DEF14E81A3249FBF21170AB8A9DEB386CD9CAADA395A10DEB3FB453-1
-------------------  ---------------------------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_swap_repay(self):
        result = run_test(
            "osmo1p0uesu8nf4fgh8xxmper5gqthd4wz6xtkyg24c",
            "ACCF5C318BF85B21F9F85276A9F0EC246022E204988D21CC503DC4E67824CE57"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-10-15 17:40:53  SPEND                                        0.000018000  OSMO           0.032735  OSMO          ACCF5C318BF85B21F9F85276A9F0EC246022E204988D21CC503DC4E67824CE57-0
2024-10-15 17:40:53  TRADE    30.812964        USDC               4.913376     stTIA                                  ACCF5C318BF85B21F9F85276A9F0EC246022E204988D21CC503DC4E67824CE57-1-0
2024-10-15 17:40:53  REPAY                                        30.812964    USDC                                   ACCF5C318BF85B21F9F85276A9F0EC246022E204988D21CC503DC4E67824CE57-1-1
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_deposit(self):
        result = run_test(
            "osmo1vqzn2kzjnhvn02x0xc5n3z2wwaw766asywjlps",
            "E86D666664D6280990601CC98FBA45C1528DB8AA8BD6AB986623280A37772B1A"
        )
        correct_result = """
-------------------  -------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
timestamp            tx_type        received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-10-17 21:59:39  SPEND                                              0.000018000  OSMO           0.004555  OSMO          E86D666664D6280990601CC98FBA45C1528DB8AA8BD6AB986623280A37772B1A-0
2024-10-17 21:59:39  _MARS_DEPOSIT                                                                                          E86D666664D6280990601CC98FBA45C1528DB8AA8BD6AB986623280A37772B1A-1-0
-------------------  -------------  ---------------  -----------------  -----------  -------------  --------  ------------  --------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

        result = run_test_verbose(
            "osmo1vqzn2kzjnhvn02x0xc5n3z2wwaw766asywjlps",
            "E86D666664D6280990601CC98FBA45C1528DB8AA8BD6AB986623280A37772B1A",
        )
        self.assertTrue("deposit 0.00067076 WBTC" in result)
