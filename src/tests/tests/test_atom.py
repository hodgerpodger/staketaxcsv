"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest

import staketaxcsv.report_atom
from staketaxcsv.atom.config_atom import localconfig
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import TICKER_ATOM
from tests.utils_ibc import apply_ibc_patches, load_tx


@apply_ibc_patches
def run_test(wallet_address, txid):
    elem = load_tx(wallet_address, txid, staketaxcsv.report_atom._txdata().get_tx)
    exporter = Exporter(wallet_address, localconfig, TICKER_ATOM)
    staketaxcsv.atom.processor.process_tx(wallet_address, elem, exporter)
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

    def test_withdraw_rewards_with_st_coins(self):
        result = run_test(
            "cosmos12ftp45z2mj8skpv355hyexfrtq5dp4gz8pzwpt",
            "14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee       fee_currency  txid
2023-12-30 07:57:59  STAKING  0.000028000      NTRN                                           0.004073  ATOM          14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000010000      stOSMO                                                                 14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000025000      STRD                                                                   14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000024000      stSTARS                                                                14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000001000      stJUNO                                                                 14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000000025      stINJ                                                                  14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000001000      stATOM                                                                 14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000015306      stEVMOS                                                                14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000013000      stUMEE                                                                 14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000002000      stCMDX                                                                 14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.000018000      USDC                                                                   14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
2023-12-30 07:57:59  STAKING  0.012508         ATOM                                                                   14BCA0CFC636254E79F090BCB6F07176E5A721B6ED5FA36A60EDFF5829153DCC-0
-------------------  -------  ---------------  -----------------  -----------  -------------  --------  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_restake_multiple_withdraw_reward(self):
        result = run_test(
            "cosmos1c5j58jxg9y7yeehwun8mtkcrpu6aks5fw654l0",
            "BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628"
        )
        correct_result = """
-------------------  -------  --------------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
timestamp            tx_type  received_amount       received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-01-06 17:43:52  STAKING  0.000000027           stINJ                                                             BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000014333           stEVMOS                                                           BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.013529999999999999  ATOM                                                              BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000090000           NTRN                                                              BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000012000           stOSMO                                                            BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000026000           STRD                                                              BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000019000           stSTARS                                                           BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000001000           stJUNO                                                            BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000001000           stATOM                                                            BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000015000           stUMEE                                                            BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000003000           stCMDX                                                            BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
2024-01-06 17:43:52  STAKING  0.000014000           USDC                                                              BBA8952489D33C0E4FF373660DBDF1908C42E325991612E0BD57B7F7A3C30628-0
-------------------  -------  --------------------  -----------------  -----------  -------------  ---  ------------  ------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
