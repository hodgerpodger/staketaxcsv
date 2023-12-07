"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest
from unittest.mock import patch

from tests.mock_algo import MockIndexer
import staketaxcsv.report_algo


@patch("staketaxcsv.report_algo.Indexer", new=MockIndexer)
def run_test(wallet_address, txid):
    exporter = staketaxcsv.report_algo.txone(wallet_address, txid)
    return exporter.export_for_test()


class TestAlgo(unittest.TestCase):

    def test_transfer_out(self):
        result = run_test(
            "HVRMBK4GHNUNDOS7J4FWALCZE7QQYN4QFA3OUP362PCHKHXYADYGZHGOOA",
            "X2LZ3HZD2SXVGP6WATFEDVALZ3DQL7JQK5ZM75NUX22RSRTVVZOA"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  -----  ------------  ----------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee    fee_currency  txid
2023-12-06 21:59:02  TRANSFER                                      257.733      ALGO           0.001  ALGO          X2LZ3HZD2SXVGP6WATFEDVALZ3DQL7JQK5ZM75NUX22RSRTVVZOA
-------------------  --------  ---------------  -----------------  -----------  -------------  -----  ------------  ----------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_in(self):
        result = run_test(
            "5GW5VO4JNTHXVH2DYV7HAKBKGQFSCAI4MBUD5EN3FLBGLF4KKRXJE24ASI",
            "X2LZ3HZD2SXVGP6WATFEDVALZ3DQL7JQK5ZM75NUX22RSRTVVZOA"
        )

        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-12-06 21:59:02  TRANSFER  257.733          ALGO                                                              X2LZ3HZD2SXVGP6WATFEDVALZ3DQL7JQK5ZM75NUX22RSRTVVZOA
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
