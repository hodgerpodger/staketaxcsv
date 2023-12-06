"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest
from unittest.mock import patch

from staketaxcsv.settings_csv import TICKER_OSMO
from staketaxcsv.api import transaction
from tests.mock_query import mock_query_one_arg
from staketaxcsv.osmo.api_data import get_tx as my_get_tx


def mock_get_tx(txid):
    return mock_query_one_arg(my_get_tx, txid, TICKER_OSMO)


@patch("staketaxcsv.osmo.api_data.get_tx", mock_get_tx)
def run_test(wallet_address, txid):
    return transaction(TICKER_OSMO, wallet_address, txid, "test")


class TestOsmo(unittest.TestCase):

    def test_redelegate(self):
        result = run_test(
            "osmo1xqgyn7q534lckptdncvhwpzv09tfrsxrf3k4zr",
            "7C7747CD7EE2F7277EB0B84008C556BBBA24EA7C3FD746716F42ED17EE7D2C17"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2023-12-01 22:22:23  STAKING  0.000024000      OSMO                                           0.014451  OSMO          7C7747CD7EE2F7277EB0B84008C556BBBA24EA7C3FD746716F42ED17EE7D2C17-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_multi_delegate_in_one_tx(self):
        result = run_test(
            "osmo1jdx4rukctmdw7ad6xw5zjrlqchyj4kt632t2rn",
            "DBB87D066C7052E36AB8A5BD4035F7270A4ABE615158DEFF4CEF3E30E3F84FB8"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2023-12-01 22:18:02  STAKING  6.919062         OSMO                                           0.006606  OSMO          DBB87D066C7052E36AB8A5BD4035F7270A4ABE615158DEFF4CEF3E30E3F84FB8-0
2023-12-01 22:18:02  STAKING  0.624267         OSMO                                                                   DBB87D066C7052E36AB8A5BD4035F7270A4ABE615158DEFF4CEF3E30E3F84FB8-1
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
