"""
usage: python3 staketaxcsv/report_stars.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/STARS*.csv

TODO: STARS CSVs are only in experimental state.  All "execute contract" transactions are still treated as
      unknown transactions.
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.common.ibc.api_rpc_multinode
import staketaxcsv.stars.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import STARS_NODE, TICKER_STARS, STARS_RPC_NODES
from staketaxcsv.stars.config_stars import localconfig
from staketaxcsv.stars.progress_stars import SECONDS_PER_PAGE, ProgressStars, SECONDS_PER_TX


def main():
    report_util.main_default(TICKER_STARS)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1(STARS_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_rpc_multinode.get_tx(STARS_RPC_NODES, txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_STARS)
    txinfo = staketaxcsv.stars.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    num_pages, num_txs = staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(
        STARS_RPC_NODES, wallet_address, max_txs)

    return SECONDS_PER_PAGE * num_pages + SECONDS_PER_TX * num_txs


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressStars()
    exporter = Exporter(wallet_address, localconfig, TICKER_STARS)

    # Fetch count of transactions to estimate progress beforehand
    staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(
        STARS_RPC_NODES, wallet_address, max_txs, progress)

    # Fetch transactions
    elems = staketaxcsv.common.ibc.api_rpc_multinode.get_txs_all(STARS_RPC_NODES, wallet_address, progress, max_txs)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.stars.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
