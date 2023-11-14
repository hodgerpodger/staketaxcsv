"""
usage: python3 staketaxcsv/report_celestia.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/CELESTIA*.csv
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd_v2
import staketaxcsv.celestia.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.celestia.config_celestia import localconfig
from staketaxcsv.celestia.genesis_airdrop import genesis_airdrop
from staketaxcsv.celestia.progress_celestia import SECONDS_PER_PAGE, ProgressCelestia
from staketaxcsv.settings_csv import CELESTIA_NODE, TICKER_CELESTIA


def main():
    report_util.main_default(TICKER_CELESTIA)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd_v2.LcdAPI_v2(CELESTIA_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_lcd_v2.LcdAPI_v2(CELESTIA_NODE).get_tx(txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_CELESTIA)
    txinfo = staketaxcsv.celestia.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_lcd_v2.get_txs_pages_count(CELESTIA_NODE, wallet_address, max_txs)


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressCelestia()
    exporter = Exporter(wallet_address, localconfig, TICKER_CELESTIA)

    # Fetch/add genesis airdrop to csv
    progress.report_message("Fetching genesis airdrop amount...")
    staketaxcsv.celestia.genesis_airdrop.genesis_airdrop(wallet_address, exporter)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = staketaxcsv.common.ibc.api_lcd_v2.get_txs_pages_count(CELESTIA_NODE, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = staketaxcsv.common.ibc.api_lcd_v2.get_txs_all(CELESTIA_NODE, wallet_address, progress, max_txs, debug=localconfig.debug)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.celestia.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
