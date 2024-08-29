"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest

import staketaxcsv.report_saga
from staketaxcsv.saga.genesis import genesis_airdrop
from staketaxcsv.saga.config_saga import localconfig
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import TICKER_SAGA
from tests.utils_ibc import apply_ibc_patches, load_tx
from tests.settings_test import specialtest


@apply_ibc_patches
def run_test(wallet_address, txid):
    elem = load_tx(wallet_address, txid, staketaxcsv.report_saga._txdata().get_tx)
    exporter = Exporter(wallet_address, localconfig, TICKER_SAGA)
    staketaxcsv.saga.processor.process_tx(wallet_address, elem, exporter)
    return exporter.export_for_test()


class TestSaga(unittest.TestCase):

    @specialtest
    def test_saga_genesis_airdrop(self):
        wallet_address = "saga1advd4mq7utk2w4pqdtjyfhn5gu4pkvnlc6mqrk"
        exporter = Exporter(wallet_address, localconfig, TICKER_SAGA)
        genesis_airdrop(wallet_address, exporter)
        result = exporter.export_for_test()

        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  --------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-04-08 00:00:00  AIRDROP  250.0            SAGA                                                              saga_genesis_airdrop
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  --------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_delegate_with_reward(self):
        result = run_test(
            "saga152sejycmayk0ffs9dm934y6ppne7lhe2vuuhwv",
            "D2A68EDF0AD423387EE3CD4F6413939E09D8504B9BBD02B660D158A64870287C"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  -------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee      fee_currency  txid
2024-08-25 13:44:00  STAKING  0.001672         SAGA                                           0.00488  SAGA          D2A68EDF0AD423387EE3CD4F6413939E09D8504B9BBD02B660D158A64870287C-0
-------------------  -------  ---------------  -----------------  -----------  -------------  -------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_withdraw_reward(self):
        result = run_test(
            "saga1cc97gwjpx5mlyeznptnn9x0hvwgzcy6jvkl8zv",
            "0D461A0A257D444F094BDCAA5770AA43562E688BF4E0DF2DB9B2F7B3EE2BD8D7"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-08-25 13:36:04  STAKING  0.702922         SAGA                                           0.003342  SAGA          0D461A0A257D444F094BDCAA5770AA43562E688BF4E0DF2DB9B2F7B3EE2BD8D7-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_in(self):
        result = run_test(
            "saga186kh7c0k0gh4ww0wh4jqc4yhzu7n7dhsc3dh9e",
            "8C37753C8B90F3065AD6DE9263D3182478096B2AB320C5315606B99712F5ED9D"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-08-25 13:45:07  TRANSFER  850.905          SAGA                                                              8C37753C8B90F3065AD6DE9263D3182478096B2AB320C5315606B99712F5ED9D-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_out(self):
        result = run_test(
            "saga1uskfr6grywpszw7787mz46evjdh4teux60r07l",
            "8C37753C8B90F3065AD6DE9263D3182478096B2AB320C5315606B99712F5ED9D"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  -----  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee    fee_currency  txid
2024-08-25 13:45:07  TRANSFER                                      850.905      SAGA           0.005  SAGA          8C37753C8B90F3065AD6DE9263D3182478096B2AB320C5315606B99712F5ED9D-0
-------------------  --------  ---------------  -----------------  -----------  -------------  -----  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
