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

    def test_place_claim_limit_cancel_series(self):
        result = run_test_txids("osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2", [
            "597E47AD52B2AD502E895D23CA66C9A69CE52C58A924ADA2CFE344BA50C3272A",  # place limit
            "8C69A5942F64CEF9C440A48878568F502B8503DADBCF61BA6256E4273AA0E96B",  # claim limit, cancel (2 msg)
        ])
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-08-06 22:51:20  SPEND                                        0.000612000  OSMO                                   597E47AD52B2AD502E895D23CA66C9A69CE52C58A924ADA2CFE344BA50C3272A
2024-08-07 06:46:44  TRADE    1.116519         USDC               0.00767866   SOL            0.001285  OSMO          8C69A5942F64CEF9C440A48878568F502B8503DADBCF61BA6256E4273AA0E96B-0
2024-08-07 06:46:44  SPEND                                        0.001285     OSMO                                   8C69A5942F64CEF9C440A48878568F502B8503DADBCF61BA6256E4273AA0E96B
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_claim_limit(self):
        result = run_test(
            "osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2",
            "1BC7CE7F34736112D2650A25223DEC0A54512F5FB44B38ADB9AD6C08F49F6CD4"
        )
        correct_result = """
-------------------  -------  --------------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount       received_currency  sent_amount  sent_currency  fee   fee_currency  txid
2024-08-30 15:01:41  TRADE    0.057998839907192574  INJ                1.0          USDC           0.01  OSMO          1BC7CE7F34736112D2650A25223DEC0A54512F5FB44B38ADB9AD6C08F49F6CD4-0
-------------------  -------  --------------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_batch_claim_does_not_include_unrelated_wallets(self):
        result = run_test(
            "osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2",
            "E750CDCC61724F7FF51AFD02BA8666E1EEDC4132355B9711E706DAB950248FB4"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee   fee_currency  txid
2024-08-15 05:17:17  TRADE    0.000001000      AKT                1.0          USDC           0.01  OSMO          E750CDCC61724F7FF51AFD02BA8666E1EEDC4132355B9711E706DAB950248FB4-0
-------------------  -------  ---------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_place_and_batch_claim_single_order(self):
        result = run_test_txids("osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2", [
            "611917EDBB374961A3E6709815D70CF2A344E8A581A008C707CCF62D0DBA2AC1",  # place limit
            "2F563F99CB3D78E0C6CBFA3002ED6E27E0E6E95E95D1BE5D1D49C022916759DD",  # batch claim (single order)
        ])
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee   fee_currency  txid
2024-08-12 19:54:10  SPEND                                        0.000618000  OSMO                               611917EDBB374961A3E6709815D70CF2A344E8A581A008C707CCF62D0DBA2AC1
2024-08-13 18:21:54  TRADE    12.49875         OSMO               5.0          USDC           0.01  OSMO          2F563F99CB3D78E0C6CBFA3002ED6E27E0E6E95E95D1BE5D1D49C022916759DD-0
-------------------  -------  ---------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_batch_claim_multiple_currencies(self):
        result = run_test(
            "osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2",
            "648D118DC6739922FF6E63811C6E655572AC6CDF542AF6C0270CCF9585FA8A86"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee   fee_currency  txid
2024-08-13 17:35:34  TRADE    0.588172         USDC               0.000009970  WBTC           0.01  OSMO          648D118DC6739922FF6E63811C6E655572AC6CDF542AF6C0270CCF9585FA8A86-0
2024-08-13 17:35:34  TRADE    0.000082540      WBTC               4.99367      USDC                               648D118DC6739922FF6E63811C6E655572AC6CDF542AF6C0270CCF9585FA8A86-0
2024-08-13 17:35:34  TRADE    5.693731         USDC               0.000099900  WBTC                               648D118DC6739922FF6E63811C6E655572AC6CDF542AF6C0270CCF9585FA8A86-0
-------------------  -------  ---------------  -----------------  -----------  -------------  ----  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
