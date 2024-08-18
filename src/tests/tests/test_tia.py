"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""
import unittest

from staketaxcsv.tia.genesis_airdrop import genesis_airdrop
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.tia.config_tia import localconfig
from staketaxcsv.settings_csv import TICKER_TIA
from tests.settings_test import specialtest
import staketaxcsv.report_tia
from tests.utils_ibc import load_tx, apply_ibc_patches


@apply_ibc_patches
def run_test(wallet_address, txid):
    elem = load_tx(wallet_address, txid, staketaxcsv.report_tia._txdata().get_tx)
    exporter = Exporter(wallet_address, localconfig, TICKER_TIA)
    staketaxcsv.tia.processor.process_tx(wallet_address, elem, exporter)
    return exporter.export_for_test()


class TestTia(unittest.TestCase):

    @specialtest
    def test_genesis_airdrop(self):
        wallet_address = "celestia1002cc5zkqvlvennxy5a5jrkywa052gdhdrqrlz"
        exporter = Exporter(wallet_address, localconfig, TICKER_TIA)
        genesis_airdrop(wallet_address, exporter)
        result = exporter.export_for_test()

        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-10-31 14:00:00  AIRDROP  257.98           TIA                                                               celestia_genesis_airdrop
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_out(self):
        result = run_test(
            "celestia1002cc5zkqvlvennxy5a5jrkywa052gdhdrqrlz",
            "F28DA9717018E07460E19882E5EE31B82E62C9734F23CF48FFED0CD11704C8D7"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2023-10-31 22:26:00  TRANSFER                                      3.0          TIA            0.021757  TIA           F28DA9717018E07460E19882E5EE31B82E62C9734F23CF48FFED0CD11704C8D7-0
-------------------  --------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_transfer_in(self):
        result = run_test(
            "celestia1fd3mclxp4e2fh0wpau3eg55x2fsm7yjxzg29j2",
            "F28DA9717018E07460E19882E5EE31B82E62C9734F23CF48FFED0CD11704C8D7"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2023-10-31 22:26:00  TRANSFER  3.0              TIA                                                               F28DA9717018E07460E19882E5EE31B82E62C9734F23CF48FFED0CD11704C8D7-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_delegate_no_reward(self):
        result = run_test(
            "celestia1keardu3hsg6kjj253gmgquu8ml4xuws4wve6zz",
            "E3771EF7BA92EE3EAC6474656A3AE3103DBCF0EEE5B939854D21A1823A7C517B"
        )
        correct_result = """
-------------------  ------------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type       received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-01-10 02:41:16  _MsgDelegate                                                                  0.001933  TIA           E3771EF7BA92EE3EAC6474656A3AE3103DBCF0EEE5B939854D21A1823A7C517B-0
-------------------  ------------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_redelegate_with_reward(self):
        result = run_test(
            "celestia1nsen97qhzqavwkn64vhyc09pst3sc4wk8dqnsm",
            "A6C2A166182956786247ED4059FE8927FE3F908DCA588CD0DA580DD00B5DEE77"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2024-01-10 02:42:15  STAKING  0.003393         TIA                                            0.005918  TIA           A6C2A166182956786247ED4059FE8927FE3F908DCA588CD0DA580DD00B5DEE77-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_ibc_transfer_in(self):
        result = run_test(
            "celestia1ffmdfxzq5yyps9m8vfle526qg4a3nmfjejygv5",
            "DF1995836FFAE1FDE5444C018DFFCBA1C154774439EF9365BF6FCB3D871A0B37"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-01-10 02:56:40  TRANSFER  10.715721        TIA                                                               DF1995836FFAE1FDE5444C018DFFCBA1C154774439EF9365BF6FCB3D871A0B37-1
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
