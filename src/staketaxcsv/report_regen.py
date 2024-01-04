"""
usage: python3 staketaxcsv/report_regen.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/regen*.csv
"""

import logging

from staketaxcsv.regen.config_regen import localconfig
from staketaxcsv.regen.progress_regen import SECONDS_PER_PAGE, ProgressRegen
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import TICKER_REGEN, REGEN_NODE
from staketaxcsv.common.ibc import api_lcd
import staketaxcsv.regen.processor
import staketaxcsv.common.ibc.api_lcd_v1


def main():
    report_util.main_default(TICKER_REGEN)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(REGEN_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = api_lcd.make_lcd_api(REGEN_NODE).get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_REGEN)
    txinfo = staketaxcsv.regen.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * api_lcd.get_txs_pages_count(REGEN_NODE, wallet_address, max_txs)


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressRegen()
    exporter = Exporter(wallet_address, localconfig, TICKER_REGEN)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = api_lcd.get_txs_pages_count(REGEN_NODE, wallet_address, max_txs)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = api_lcd.get_txs_all(
        REGEN_NODE, wallet_address, progress, max_txs)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.regen.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
