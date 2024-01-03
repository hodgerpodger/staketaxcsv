"""
usage: python3 staketaxcsv/report_atom.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ATOM*.csv


Notes:

https://node.atomscan.com/swagger/

"""

import logging
import math


import staketaxcsv.api
import staketaxcsv.atom.api_lcd
import staketaxcsv.atom.cosmoshub123.api_cosmostation
import staketaxcsv.atom.processor
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.atom.config_atom import localconfig
from staketaxcsv.atom.progress_atom import SECONDS_PER_PAGE, ProgressAtom
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import ATOM_NODE, TICKER_ATOM

LIMIT_PER_QUERY = 50


def main():
    report_util.main_default(TICKER_ATOM)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)

    localconfig.legacy = options.get("legacy", False)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.atom.api_lcd.account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = api_lcd.get_tx(ATOM_NODE, txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_ATOM)
    txinfo = staketaxcsv.atom.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * api_lcd.get_txs_pages_count(ATOM_NODE, wallet_address, max_txs)


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressAtom()
    exporter = Exporter(wallet_address, localconfig, TICKER_ATOM)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = api_lcd.get_txs_pages_count(ATOM_NODE, wallet_address, max_txs)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = api_lcd.get_txs_all(ATOM_NODE, wallet_address, progress, max_txs, debug=localconfig.debug)

    progress.report_message(f"Processing {len(elems)} ATOM transactions... ")
    staketaxcsv.atom.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
