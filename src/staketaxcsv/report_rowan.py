"""
usage: python3 staketaxcsv/report_rowan.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ROWAN*.csv
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.rowan.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import ROWAN_NODE, TICKER_ROWAN
from staketaxcsv.rowan.config_rowan import localconfig
from staketaxcsv.rowan.progress_rowan import SECONDS_PER_PAGE, ProgressRowan
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.tx_data import TxDataLcd
from staketaxcsv.common.ibc.decorators import set_ibc_cache


def main():
    report_util.main_default(TICKER_ROWAN)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataLcd(ROWAN_NODE, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(ROWAN_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_ROWAN)
    txinfo = staketaxcsv.rowan.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


@set_ibc_cache()
def txhistory(wallet_address):
    progress = ProgressRowan()
    exporter = Exporter(wallet_address, localconfig, TICKER_ROWAN)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.rowan.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
