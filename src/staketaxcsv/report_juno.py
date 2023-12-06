"""
usage: python3 staketaxcsv/report_juno.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/JUNO*.csv

TODO: JUNO CSVs are only in experimental state.  All "execute contract" transactions are still treated as
      unknown transactions.
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.common.ibc.api_rpc
import staketaxcsv.common.ibc.api_rpc_multinode
import staketaxcsv.juno.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.juno.config_juno import localconfig
from staketaxcsv.juno.progress_juno import SECONDS_PER_PAGE, ProgressJuno, SECONDS_PER_TX
from staketaxcsv.settings_csv import JUNO_NODE, TICKER_JUNO, JUNO_RPC_NODES


def main():
    report_util.main_default(TICKER_JUNO)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1(JUNO_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_rpc_multinode.get_tx(JUNO_RPC_NODES, txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_JUNO)
    txinfo = staketaxcsv.juno.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    num_pages, num_txs = staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(
        JUNO_RPC_NODES, wallet_address, max_txs)

    return SECONDS_PER_PAGE * num_pages + SECONDS_PER_TX * num_txs


def txhistory(wallet_address):
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressJuno()
    exporter = Exporter(wallet_address, localconfig, TICKER_JUNO)

    # Fetch count of transactions to estimate progress beforehand
    staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(
        JUNO_RPC_NODES, wallet_address, max_txs, progress)

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
