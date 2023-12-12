
import unittest
from unittest.mock import patch

from tests.mock_sol import MockRpcAPI, MockHeliusAPI
import staketaxcsv.report_sol


@patch("staketaxcsv.sol.parser.RpcAPI", new=MockRpcAPI)
@patch("staketaxcsv.report_sol.RpcAPI", new=MockRpcAPI)
@patch("staketaxcsv.sol.api_helius.HeliusAPI", new=MockHeliusAPI)
def run_test(wallet_address, txid):
    exporter = staketaxcsv.report_sol.txone(wallet_address, txid)
    return exporter.export_for_test()
