"""
usage: python3 staketaxcsv/report_generic_lcd.py <walletaddress> --generic_node <url_lcd_node> --generic_ticker <token_symbol> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/<ticker>*.csv

Notes:

* Example usage:
   python3 staketaxcsv/report_generic_lcd.py akash19yy53sz8ed88me79neeksqra06kcs5ly24758d --generic_node https://rest-akash.ecostake.com --generic_ticker AKT
* See https://github.com/cosmos/chain-registry to find LCD nodes (search "rest" in chain.json)

"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd
import staketaxcsv.generic.processor
from settings_csv import TICKER_GENERIC
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.generic.config_generic import localconfig
from staketaxcsv.generic.progress_generic import SECONDS_PER_PAGE, ProgressGeneric
from common.ibc.constants import MINTSCAN_LABELS


def main():
    report_util.main_default(TICKER_GENERIC)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)

    localconfig.node = options["generic_node"]
    localconfig.ticker = options.get("generic_ticker", localconfig.ticker)
    localconfig.mintscan_label = MINTSCAN_LABELS.get(localconfig.ticker, "generic")

    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd.LcdAPI(localconfig.node).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_lcd.LcdAPI(localconfig.node).get_tx(txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_GENERIC)
    txinfo = staketaxcsv.generic.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(
        localconfig.node, wallet_address, max_txs)


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressGeneric()
    exporter = Exporter(wallet_address, localconfig, TICKER_GENERIC)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(
        localconfig.node, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = staketaxcsv.common.ibc.api_lcd.get_txs_all(
        localconfig.node, wallet_address, progress, max_txs, debug=localconfig.debug)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.generic.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
