"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import logging
import unittest
from tests.utils_osmo import run_test


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

    def test_swap_v202401(self):
        result = run_test(
            "osmo1r0sadvrq6f42uqkvppe0aew34kfn4daghncgmu",
            "37F8F96EA91C830B201797EC148D97F69FB2322CB7E1EE66DEE5A84C3560F091"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-01-01 00:24:07  TRADE    12.536491        OSMO               1.6          TIA            0.012629  OSMO          37F8F96EA91C830B201797EC148D97F69FB2322CB7E1EE66DEE5A84C3560F091-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_ibc_transfer_in(self):
        logging.basicConfig(level=logging.INFO)

        result = run_test(
            "osmo1f06vhp6m9fkghfpgafqwuetys9u74gy7eurz86",
            "43D62F41B6B0128C304C38BFC69D13CE2C3BE119E1866906E43F557FCF39F07F"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-01-11 19:09:39  TRANSFER  3.957272         milkTIA                                                           43D62F41B6B0128C304C38BFC69D13CE2C3BE119E1866906E43F557FCF39F07F-2
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_ibc_transfer_out(self):
        result = run_test(
            "osmo1f06vhp6m9fkghfpgafqwuetys9u74gy7eurz86",
            "5BFEADF2D10FE460AF00BA60D07B16B65063EA0EA90AF67FB55853EF88E125F4"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee     fee_currency  txid
2024-01-11 19:25:19  TRANSFER                                      3.957272     milkTIA        0.0125  OSMO          5BFEADF2D10FE460AF00BA60D07B16B65063EA0EA90AF67FB55853EF88E125F4-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_authz_grant(self):
        result = run_test(
            "osmo1u3xlchr8rvmaxfuh6n2nsnj5phpc3k5dpdww6m",
            "5AD1012BC3454AD4CFD432F839E5DBA5E6367F313108CE3142C1516C5A31839B"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-07-20 01:00:22  SPEND                                        0.000468000  OSMO           0                  5AD1012BC3454AD4CFD432F839E5DBA5E6367F313108CE3142C1516C5A31839B-0
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_authz_revoke(self):
        result = run_test(
            "osmo1u3xlchr8rvmaxfuh6n2nsnj5phpc3k5dpdww6m",
            "E4313FADC11DFF2BB39B2BA284534C9E09BED770E2138CB2A9D1131FEA8D6940"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-07-02 14:29:04  SPEND                                        0.000322000  OSMO           0                  E4313FADC11DFF2BB39B2BA284534C9E09BED770E2138CB2A9D1131FEA8D6940-0
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
