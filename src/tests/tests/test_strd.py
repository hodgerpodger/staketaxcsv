"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from unittest.mock import patch

from tests.mock_lcd import MockLcdAPI_v1, MockLcdAPI_v2
from tests.mock_mintscan import MockMintscanAPI
import staketaxcsv.report_strd


@patch("staketaxcsv.common.ibc.denoms.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v2.LcdAPI_v2", new=MockLcdAPI_v2)
@patch("staketaxcsv.common.ibc.tx_data.MintscanAPI", new=MockMintscanAPI)
@patch("staketaxcsv.settings_csv.DB_CACHE", False)
def run_test(wallet_address, txid):
    exporter = staketaxcsv.report_strd.txone(wallet_address, txid)
    return exporter.export_for_test()


class TestStrd(unittest.TestCase):

    def test_ibc_transfer_multi_in_multi_out(self):
        result = run_test(
            "stride1hc6kkysu2kwx3ls0nhw29sw69wc9qx892xupmf",
            "6A136A5D57541E6BE5C09001EA61EC432472AB234ED6430A0F2C1139A3AECA73"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-07-02 07:44:30  TRANSFER  0.008527         stATOM                                                            6A136A5D57541E6BE5C09001EA61EC432472AB234ED6430A0F2C1139A3AECA73-1
2023-07-02 07:44:30  TRANSFER  7.62085          STRD                                                              6A136A5D57541E6BE5C09001EA61EC432472AB234ED6430A0F2C1139A3AECA73-1
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_liquid_stake(self):
        result = run_test(
            "stride1hc6kkysu2kwx3ls0nhw29sw69wc9qx892xupmf",
            "ED0F17700E65792D8372B197A660D9423E681D8575F170EE58566B8DB9E9C85D"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2022-11-23 12:53:15  TRADE    0.009645         stATOM             0.01         ATOM                              ED0F17700E65792D8372B197A660D9423E681D8575F170EE58566B8DB9E9C85D-0
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_liquid_stake_with_multi_rewards(self):
        result = run_test(
            "stride10jsw8uvkajrd299k5k3y9s3kxlfsj0skqkqxnk",
            "65F7196CBDA2A1EEA9F9B2791DD30C0ED0A16C364CEB58933C5A33D4865AD397"
        )
        correct_result = """
-------------------  -------  ------------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount     received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-02-28 16:21:43  STAKING  20.235576000000002  STRD                                                              65F7196CBDA2A1EEA9F9B2791DD30C0ED0A16C364CEB58933C5A33D4865AD397-0
2023-02-28 16:21:43  TRADE    45.700027           stATOM             50.0         ATOM                              65F7196CBDA2A1EEA9F9B2791DD30C0ED0A16C364CEB58933C5A33D4865AD397-0
-------------------  -------  ------------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
