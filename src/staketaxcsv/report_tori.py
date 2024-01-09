"""
usage: python3 staketaxcsv/report_tori.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/TORI*.csv
"""

import logging
import pprint

import staketaxcsv.tori.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import TORI_NODE, TICKER_TORI
from staketaxcsv.tori.config_tori import localconfig
from staketaxcsv.tori.progress_tori import SECONDS_PER_PAGE, ProgressTori
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.tx_data import TxDataLcd


def main():
    report_util.main_default(TICKER_TORI)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataLcd(TORI_NODE, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(TORI_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_TORI)
    txinfo = staketaxcsv.tori.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    progress = ProgressTori()
    exporter = Exporter(wallet_address, localconfig, TICKER_TORI)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.tori.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
