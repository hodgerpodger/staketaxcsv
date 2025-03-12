"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""
import unittest

from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.sei.config_sei import localconfig
from staketaxcsv.settings_csv import TICKER_SEI
from tests.settings_test import specialtest
import staketaxcsv.report_sei
from tests.utils_ibc import load_tx, apply_ibc_patches


@apply_ibc_patches
def run_test(wallet_address, txid):
    elem = load_tx(wallet_address, txid, staketaxcsv.report_sei._txdata().get_tx)
    exporter = Exporter(wallet_address, localconfig, TICKER_SEI)
    staketaxcsv.sei.processor.process_tx(wallet_address, elem, exporter)
    return exporter.export_for_test()


class TestTia(unittest.TestCase):

    def test_transfer_out(self):
        result = run_test(
            "sei1e22msazh4pmdzvpckzfsth37ys4c4yh85dcg8q",
            "0B77D11BD9E0C551A8CC7C6144ABF8BCC22D9BB5CD2DB68A91CA70FA8C7138EC"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2025-02-15 23:24:19  TRANSFER                                      209056.0     SEI            0.080208  SEI           0B77D11BD9E0C551A8CC7C6144ABF8BCC22D9BB5CD2DB68A91CA70FA8C7138EC-0
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_in(self):
        result = run_test(
            "sei1phjkp88amtkh9wh3u6296c90ekuhewlt0h8ztg",
            "7AF2329AF42836CF9493625FCCE1DF24B4589EF36F057DC88937C8D0153FFE72"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-09-18 18:33:16  TRANSFER  9.0              SEI                                                               7AF2329AF42836CF9493625FCCE1DF24B4589EF36F057DC88937C8D0153FFE72-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_delegate_no_reward(self):
        result = run_test(
            "sei1e22msazh4pmdzvpckzfsth37ys4c4yh85dcg8q",
            "3101A6D21C2D0579580C14E65DD9FBBC4B76C14E6C48E520C975D196575334FB"
        )
        correct_result = """
-------------------  ------------  ---------------  -----------------  -----------  -------------  ------  ------------  ------------------------------------------------------------------
timestamp            tx_type       received_amount  received_currency  sent_amount  sent_currency  fee     fee_currency  txid
2023-08-30 21:22:16  _MsgDelegate                                                                  0.0429  SEI           3101A6D21C2D0579580C14E65DD9FBBC4B76C14E6C48E520C975D196575334FB-0
-------------------  ------------  ---------------  -----------------  -----------  -------------  ------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_delegate_with_reward(self):
        result = run_test(
            "sei1axmqyvccsdvsgga2g7lajmj2dqtu2uusl0pz8e",
            "D33EA9DDFAB3BDB2499FBFAA530E7D8ECC4744F5109DFD28B7B36C754F761A87"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  -------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee      fee_currency  txid
2024-12-04 20:32:34  STAKING  0.006651         SEI                                            0.00476  SEI           D33EA9DDFAB3BDB2499FBFAA530E7D8ECC4744F5109DFD28B7B36C754F761A87-0
-------------------  -------  ---------------  -----------------  -----------  -------------  -------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_redelegate_with_reward(self):
        result = run_test(
            "sei157483dnzqn9g29gvm8ppnxkq67858vhkc53et2",
            "51726FF4A92AC624083FCDE0E621256C13DAEE9D8BF6BF093FE0D1988BC96136"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2025-03-11 08:52:06  STAKING  0.529209         SEI                                            0.079612  SEI           51726FF4A92AC624083FCDE0E621256C13DAEE9D8BF6BF093FE0D1988BC96136-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_get_reward(self):
        result = run_test(
            "sei1e22msazh4pmdzvpckzfsth37ys4c4yh85dcg8q",
            "EB72983FC0EF03C59DBFBE5A5DC5048B6453483C46638190B1A3DA8AF297DD8F"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2025-02-15 15:56:17  STAKING  209054.970249    SEI                                            0.328515  SEI           EB72983FC0EF03C59DBFBE5A5DC5048B6453483C46638190B1A3DA8AF297DD8F-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
