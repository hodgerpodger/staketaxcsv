"""
usage: python3 report_juno.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/JUNO*.csv

TODO: JUNO CSVs are only in experimental state.  All "execute contract" transactions are still treated as
      unknown transactions.
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd
import staketaxcsv.common.ibc.api_rpc
import staketaxcsv.common.ibc.api_rpc_multinode
import staketaxcsv.juno.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.juno.config_juno import localconfig
from staketaxcsv.juno.progress_juno import SECONDS_PER_PAGE, ProgressJuno
from staketaxcsv.settings_csv import JUNO_NODE, TICKER_JUNO, JUNO_RPC_NODES


def main():
    report_util.main_default(TICKER_JUNO)


def read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd.LcdAPI(JUNO_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_rpc_multinode.get_tx(JUNO_RPC_NODES, txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_JUNO)
    txinfo = staketaxcsv.juno.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address, options):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(
        JUNO_RPC_NODES, wallet_address, max_txs)


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    read_options(options)
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressJuno()
    exporter = Exporter(wallet_address, localconfig, TICKER_JUNO)

    # Fetch count of transactions to estimate progress more accurately
    pages_total = staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(JUNO_RPC_NODES, wallet_address, max_txs)
    progress.set_estimate(pages_total)

    # Fetch transactions
    elems = staketaxcsv.common.ibc.api_rpc_multinode.get_txs_all(JUNO_RPC_NODES, wallet_address, progress, max_txs)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.juno.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
