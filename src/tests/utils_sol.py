
import unittest
from unittest.mock import patch

from tests.mock_sol import MockRpcAPI
import staketaxcsv.report_sol
from staketaxcsv.sol.config_sol import localconfig
from staketaxcsv.settings_csv import TICKER_SOL
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.sol.TxInfoSol import WalletInfo


@patch("staketaxcsv.sol.parser.RpcAPI", new=MockRpcAPI)
@patch("staketaxcsv.report_sol.RpcAPI", new=MockRpcAPI)
def run_test(wallet_address, txid):
    exporter = staketaxcsv.report_sol.txone(wallet_address, txid)
    return exporter.export_for_test()


@patch("staketaxcsv.sol.parser.RpcAPI", new=MockRpcAPI)
@patch("staketaxcsv.report_sol.RpcAPI", new=MockRpcAPI)
def run_test_txids(wallet_address, txids):
    exporter = Exporter(wallet_address, localconfig, TICKER_SOL)
    staketaxcsv.report_sol._fetch_and_process_txs(txids, WalletInfo(wallet_address), exporter)
    return exporter.export_for_test()
