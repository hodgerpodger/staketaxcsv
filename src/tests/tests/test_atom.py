"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from unittest.mock import patch

from tests.mock_lcd import MockLcdAPI_v1
import staketaxcsv.report_atom


@patch("staketaxcsv.report_atom.LcdAPI_v1", new=MockLcdAPI_v1)
def run_test(wallet_address, txid):
    exporter = staketaxcsv.report_atom.txone(wallet_address, txid)
    return exporter.export_for_test()


class TestAtom(unittest.TestCase):

    def test_send(self):
        result = run_test(
            "cosmos13fe2vuy0e383q64usww4v5vxkmz6gcnfwv5u7v",
            "EAE059242FB773F07526E7564065F30BB6BE85A451CF19A1D06F479F44B4EC5F"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  -------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee      fee_currency  txid
2023-12-07 03:13:04  TRANSFER                                      2.0          ATOM           0.00209  ATOM          EAE059242FB773F07526E7564065F30BB6BE85A451CF19A1D06F479F44B4EC5F-0
-------------------  --------  ---------------  -----------------  -----------  -------------  -------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_receive(self):
        result = run_test(
            "cosmos1xu3gawvpgykepm6kg4ayvs7q8zepj2jzecedax",
            "EAE059242FB773F07526E7564065F30BB6BE85A451CF19A1D06F479F44B4EC5F"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-12-07 03:13:04  TRANSFER  2.0              ATOM                                                              EAE059242FB773F07526E7564065F30BB6BE85A451CF19A1D06F479F44B4EC5F-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
