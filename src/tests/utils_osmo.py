import logging
from unittest.mock import patch

from tests.mock_osmo import mock_get_tx, mock_get_symbol, mock_get_exponent
from tests.mock_lcd import MockLcdAPI_v1
import staketaxcsv.report_osmo
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.settings_csv import TICKER_OSMO
from staketaxcsv.common.Exporter import Exporter
import staketaxcsv.osmo.api_data
import staketaxcsv.osmo.processor
from tests.mock_mintscan import MockMintscanAPI
from staketaxcsv.report_osmo import _txdata


def run_test(wallet_address, txid):
    return run_test_txids(wallet_address, [txid])


@patch("staketaxcsv.common.ibc.tx_data.MintscanAPI", new=MockMintscanAPI)
@patch("staketaxcsv.common.ibc.denoms.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1", new=MockLcdAPI_v1)
@patch("staketaxcsv.osmo.MsgInfoOsmo.get_symbol", mock_get_symbol)
@patch("staketaxcsv.osmo.MsgInfoOsmo.get_exponent", mock_get_exponent)
def run_test_txids(wallet_address, txids):
    exporter = Exporter(wallet_address, localconfig, TICKER_OSMO)

    txdata = _txdata()

    elems = []
    for txid in txids:
        elem = txdata.get_tx(txid)
        elems.append(elem)

    staketaxcsv.osmo.processor.process_txs(wallet_address, elems, exporter)

    return exporter.export_for_test()
