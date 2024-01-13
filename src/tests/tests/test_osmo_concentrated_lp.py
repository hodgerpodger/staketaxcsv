"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from tests.utils_osmo import run_test_txids


class TestOsmo(unittest.TestCase):

    def test_create_withdraw_position(self):
        wallet = "osmo1f06vhp6m9fkghfpgafqwuetys9u74gy7eurz86"
        txids = [
            "E03AA85B5F9EE2FC6E6873829A69129081225EE2095F508E31C41E2B3A2B6D2F",
            "B808DF20D8D61B574682A0E9AD4120EA05DEC449B9AA4057C20BDD189FD087BC",
        ]
        result = run_test_txids(wallet, txids)
        correct_result = """
-------------------  -----------  ------------------  -----------------  ------------------  ---------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type      received_amount     received_currency  sent_amount         sent_currency    fee       fee_currency  txid
2024-01-13 15:21:36  LP_DEPOSIT   32476347.988389455  LP_POOL_ID_1265    2.554859            ATOM             0.009413  OSMO          E03AA85B5F9EE2FC6E6873829A69129081225EE2095F508E31C41E2B3A2B6D2F-0
2024-01-13 15:21:36  LP_DEPOSIT   32476347.988389455  LP_POOL_ID_1265    9.21461             OSMO                                     E03AA85B5F9EE2FC6E6873829A69129081225EE2095F508E31C41E2B3A2B6D2F-0
2024-01-13 15:58:29  LP_WITHDRAW  9.212867            OSMO               32476347.988389455  LP_POOL_ID_1265  0.011031  OSMO          B808DF20D8D61B574682A0E9AD4120EA05DEC449B9AA4057C20BDD189FD087BC-0
2024-01-13 15:58:29  LP_WITHDRAW  2.555165            ATOM               32476347.988389455  LP_POOL_ID_1265                          B808DF20D8D61B574682A0E9AD4120EA05DEC449B9AA4057C20BDD189FD087BC-0
-------------------  -----------  ------------------  -----------------  ------------------  ---------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
