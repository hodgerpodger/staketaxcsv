"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest

import staketaxcsv.report_arch
from staketaxcsv.arch.config_arch import localconfig
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import TICKER_ARCH
from tests.utils_ibc import apply_ibc_patches, load_tx


@apply_ibc_patches
def run_test(wallet_address, txid):
    elem = load_tx(wallet_address, txid, staketaxcsv.report_arch._txdata().get_tx)
    exporter = Exporter(wallet_address, localconfig, TICKER_ARCH)
    staketaxcsv.arch.processor.process_tx(wallet_address, elem, exporter)
    return exporter.export_for_test()


class TestArch(unittest.TestCase):

    def test_delegate(self):
        result = run_test(
            "archway1w09nmhpeg3dxp649vdydn6rtrekx3k9uwuugsh",
            "4C8B7AE1E56131FB815A4BB4385AAB3EF30B80EB0FC3653B5B7C43C06F790EEC"
        )
        correct_result = """
-------------------  ------------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type       received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2023-07-04 16:25:43  _MsgDelegate                                                                  0.264583  ARCH          4C8B7AE1E56131FB815A4BB4385AAB3EF30B80EB0FC3653B5B7C43C06F790EEC-0
-------------------  ------------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_withdraw_reward(self):
        result = run_test(
            "archway1w09nmhpeg3dxp649vdydn6rtrekx3k9uwuugsh",
            "8F12B062BBE9607C1C220DCC68954530E5F18BAF7A001FD2040B32742132380B"
        )
        correct_result = """
-------------------  -------  ------------------  -----------------  -----------  -------------  ---------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount     received_currency  sent_amount  sent_currency  fee        fee_currency  txid
2023-07-09 03:56:34  STAKING  14.549436601042833  ARCH                                           0.3172965  ARCH          8F12B062BBE9607C1C220DCC68954530E5F18BAF7A001FD2040B32742132380B-0
-------------------  -------  ------------------  -----------------  -----------  -------------  ---------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_redelegate(self):
        result = run_test(
            "archway1w09nmhpeg3dxp649vdydn6rtrekx3k9uwuugsh",
            "0D3CAECAD97B664A1FBB2E11428C89673331657ACB24217F40F895A4CD213C0E"
        )
        correct_result = """
-------------------  -------  ------------------  -----------------  -----------  -------------  ---------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount     received_currency  sent_amount  sent_currency  fee        fee_currency  txid
2023-07-13 20:27:09  STAKING  11.221299726869644  ARCH                                           0.3117222  ARCH          0D3CAECAD97B664A1FBB2E11428C89673331657ACB24217F40F895A4CD213C0E-0
-------------------  -------  ------------------  -----------------  -----------  -------------  ---------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_in(self):
        result = run_test(
            "archway1w09nmhpeg3dxp649vdydn6rtrekx3k9uwuugsh",
            "5FDB607CF83F68A429695183BED967B1CED93C1750540E52AFE8BAFBC9169DB7"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-08-12 17:58:22  TRANSFER  84.0             ARCH                                                              5FDB607CF83F68A429695183BED967B1CED93C1750540E52AFE8BAFBC9169DB7-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_out(self):
        result = run_test(
            "archway1r7v4a9n8z6cxtm4rde0y9r5jz8wmh90wrrxsv8",
            "5FDB607CF83F68A429695183BED967B1CED93C1750540E52AFE8BAFBC9169DB7"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2023-08-12 17:58:22  TRANSFER                                      84.0         ARCH           0.202932  ARCH          5FDB607CF83F68A429695183BED967B1CED93C1750540E52AFE8BAFBC9169DB7-0
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
