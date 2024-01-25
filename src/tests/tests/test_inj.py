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
import staketaxcsv.report_inj


@patch("staketaxcsv.common.ibc.denoms.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v2.LcdAPI_v2", new=MockLcdAPI_v2)
@patch("staketaxcsv.common.ibc.tx_data.MintscanAPI", new=MockMintscanAPI)
@patch("staketaxcsv.settings_csv.DB_CACHE", False)
def run_test(wallet_address, txid):
    exporter = staketaxcsv.report_inj.txone(wallet_address, txid)
    return exporter.export_for_test()


class TestStrd(unittest.TestCase):

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
