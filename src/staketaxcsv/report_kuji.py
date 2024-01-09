"""
usage: python3 staketaxcsv/report_kuji.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/KUJI*.csv
"""

import logging
import pprint

import staketaxcsv.kuji.processor
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.kuji.config_kuji import localconfig
from staketaxcsv.kuji.progress_kuji import SECONDS_PER_PAGE, ProgressKuji
from staketaxcsv.settings_csv import KUJI_NODE, TICKER_KUJI
from staketaxcsv.common.ibc.tx_data import TxDataLcd
LIMIT_PER_QUERY = 15


def main():
    report_util.main_default(TICKER_KUJI)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataLcd(KUJI_NODE, max_txs, limit_per_query=LIMIT_PER_QUERY)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(KUJI_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_KUJI)
    txinfo = staketaxcsv.kuji.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    progress = ProgressKuji()
    exporter = Exporter(wallet_address, localconfig, TICKER_KUJI)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.kuji.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
