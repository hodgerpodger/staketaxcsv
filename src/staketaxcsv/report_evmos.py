"""
usage: python3 staketaxcsv/report_evmos.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/EVMOS*.csv

Note:
    * <walletaddress> can be either of 'evmos...' or '0x...' formats
"""

import logging

import staketaxcsv.common.address
import staketaxcsv.evmos.processor
from staketaxcsv.common.address import evmo_addrs
from staketaxcsv.common.ibc import api_lcd, historical_balances
from staketaxcsv.common import report_util
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.evmos.config_evmos import localconfig
from staketaxcsv.settings_csv import EVMOS_NODE, TICKER_EVMOS, MINTSCAN_ON
from staketaxcsv.common.ibc.tx_data import TxDataMintscan, TxDataLcd
from staketaxcsv.common.ibc.progress_mintscan import ProgressMintScan, SECONDS_PER_PAGE
from staketaxcsv.common.ibc.decorators import set_ibc_cache


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_EVMOS)

    # Use "evmos..." format for wallet_address before proceeding with rest of script
    wallet_address, hex_address = evmo_addrs(wallet_address)
    logging.info("wallet_address: %s, hex_address: %s", wallet_address, hex_address)

    report_util.run_report(TICKER_EVMOS, wallet_address, export_format, txid, options)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    localconfig.start_date = options.get("start_date", None)
    localconfig.end_date = options.get("end_date", None)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataMintscan(TICKER_EVMOS, max_txs) if MINTSCAN_ON else TxDataLcd(EVMOS_NODE, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(EVMOS_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_EVMOS)
    txinfo = staketaxcsv.evmos.processor.process_tx(wallet_address, elem, exporter)

    if localconfig.debug:
        print("txinfo:")
        txinfo.print()

    return exporter


def estimate_duration(wallet_address):
    start_date, end_date = localconfig.start_date, localconfig.end_date

    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address, start_date, end_date)


@set_ibc_cache()
def txhistory(wallet_address):
    start_date, end_date = localconfig.start_date, localconfig.end_date
    progress = ProgressMintScan(localconfig)
    exporter = Exporter(wallet_address, localconfig, TICKER_EVMOS)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address, start_date, end_date)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress, start_date, end_date)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.evmos.processor.process_txs(wallet_address, elems, exporter)

    return exporter


def balhistory(wallet_address):
    """ Writes historical balances CSV rows to BalExporter object """
    start_date, end_date = localconfig.start_date, localconfig.end_date
    max_txs = localconfig.limit

    exporter = historical_balances.via_mintscan(
        EVMOS_NODE, TICKER_EVMOS, wallet_address, max_txs, start_date, end_date)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
