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


@patch("staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v2.LcdAPI_v2", new=MockLcdAPI_v2)
@patch("staketaxcsv.common.ibc.tx_data.MintscanAPI", new=MockMintscanAPI)
def run_test(wallet_address, txid):
    exporter = staketaxcsv.report_strd.txone(wallet_address, txid)
    return exporter.export_for_test()


class TestStrd(unittest.TestCase):

    def test_claim_free_amount(self):
        result = run_test(
            "stride1hc6kkysu2kwx3ls0nhw29sw69wc9qx892xupmf",
            "7C314E0223AE1369ECCB250D348C51941B21A0819F99C15EC4FB4200BB2157BE"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2022-11-23 12:44:44  AIRDROP  8.533561         STRD                                                              7C314E0223AE1369ECCB250D348C51941B21A0819F99C15EC4FB4200BB2157BE-0
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

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
