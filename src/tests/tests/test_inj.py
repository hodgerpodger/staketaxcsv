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
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.inj.config_inj import localconfig
from staketaxcsv.inj import constants as co
from staketaxcsv.report_inj import _txdata
from staketaxcsv.settings_csv import TICKER_INJ
from staketaxcsv.inj.handle_deposit_claim import Deposits


def run_test(wallet_addres, txid):
    return run_test_txids(wallet_addres, [txid])


@patch("staketaxcsv.common.ibc.denoms.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v2.LcdAPI_v2", new=MockLcdAPI_v2)
@patch("staketaxcsv.common.ibc.tx_data.MintscanAPI", new=MockMintscanAPI)
@patch("staketaxcsv.settings_csv.DB_CACHE", False)
def run_test_txids(wallet_address, txids):
    exporter = Exporter(wallet_address, localconfig, TICKER_INJ)
    txdata = _txdata()

    elems = []
    for txid in txids:
        elem = txdata.get_tx(txid)
        elems.append(elem)

    staketaxcsv.inj.processor.process_txs(wallet_address, elems, exporter)
    return exporter.export_for_test()


class TestStrd(unittest.TestCase):

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
