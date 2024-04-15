import unittest

import staketaxcsv.report_dym
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.dym.config_dym import localconfig
from staketaxcsv.dym.genesis_airdrop import genesis_airdrop
from staketaxcsv.settings_csv import TICKER_DYM
from tests.settings_test import specialtest
from tests.utils_ibc import apply_ibc_patches, load_tx


@apply_ibc_patches
def run_test(wallet_address, txid):
    elem = load_tx(wallet_address, txid, staketaxcsv.report_dym._txdata().get_tx)
    exporter = Exporter(wallet_address, localconfig, TICKER_DYM)
    staketaxcsv.dym.processor.process_tx(wallet_address, elem, exporter)
    return exporter.export_for_test()


class TestDym(unittest.TestCase):

    @specialtest
    def test_dym_genesis_airdrop(self):
        wallet_address = "dym1c2mehvjjyecfqlknrn0lwp8gk2q40wxp6uyxch"
        exporter = Exporter(wallet_address, localconfig, TICKER_DYM)
        genesis_airdrop(wallet_address, exporter)
        result = exporter.export_for_test()

        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  -------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-02-06 11:00:00  AIRDROP  85.8015273411    DYM                                                               dymension_genesis_airdrop
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  -------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_eth_tx_transfer_in(self):
        result = run_test(
            "dym1gxe3ryxw8h957yghtp87as24pt66hpvee4lj52",
            "98544CCA5B3066DCE71ED6B28EE11E9261E45136E83AB9F18A122AB7990CC5F9"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-02-11 00:50:59  TRANSFER  55.8             DYM                                                               98544CCA5B3066DCE71ED6B28EE11E9261E45136E83AB9F18A122AB7990CC5F9-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_eth_tx_transfer_out(self):
        result = run_test(
            "dym1c2l43ugygxrz6qc3j38zhhvkcdrm89r9tpplu8",
            "1869529F1B04C72AE7EA1535C12680E6270DC488A914F056A783E715F592C473"
        )
        correct_result = """
-------------------  --------  ---------------  -----------------  -----------  -------------  ----------  ------------  ------------------------------------------------------------------
timestamp            tx_type   received_amount  received_currency  sent_amount  sent_currency  fee         fee_currency  txid
2024-02-07 12:51:12  TRANSFER                                      28.5         DYM            0.00197589  DYM           1869529F1B04C72AE7EA1535C12680E6270DC488A914F056A783E715F592C473-0
-------------------  --------  ---------------  -----------------  -----------  -------------  ----------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_delegate_no_reward(self):
        result = run_test(
            "dym1gxe3ryxw8h957yghtp87as24pt66hpvee4lj52",
            "E1CC55AD65485D016C5B889814915648B7DDAF5978B74D0FB1B024698120467F"
        )
        correct_result = """
-------------------  ------------  ---------------  -----------------  -----------  -------------  ----------  ------------  ------------------------------------------------------------------
timestamp            tx_type       received_amount  received_currency  sent_amount  sent_currency  fee         fee_currency  txid
2024-02-11 01:08:17  _MsgDelegate                                                                  0.00569962  DYM           E1CC55AD65485D016C5B889814915648B7DDAF5978B74D0FB1B024698120467F-0
-------------------  ------------  ---------------  -----------------  -----------  -------------  ----------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
