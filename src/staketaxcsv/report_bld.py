"""
usage: python3 staketaxcsv/report_bld.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/BLD*.csv
"""

import logging

import staketaxcsv.bld.processor
import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.common.ibc.api_rpc_multinode
from staketaxcsv.bld.config_bld import localconfig
from staketaxcsv.bld.progress_bld import SECONDS_PER_PAGE, ProgressBld, SECONDS_PER_TX
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import BLD_NODE, TICKER_BLD, BLD_RPC_NODE
BLD_RPC_NODES = [BLD_RPC_NODE]
LIMIT_TXS_PER_QUERY = 20


def main():
    report_util.main_default(TICKER_BLD)


def read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1(BLD_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_rpc_multinode.get_tx(
        BLD_RPC_NODES, txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_BLD)
    txinfo = staketaxcsv.bld.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    num_pages, num_txs = staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(
        BLD_RPC_NODES, wallet_address, max_txs, limit=LIMIT_TXS_PER_QUERY
    )

    return SECONDS_PER_PAGE * num_pages + SECONDS_PER_TX * num_txs


def txhistory(wallet_address):
    """ Configure localconfig based on options dictionary. """
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressBld()
    exporter = Exporter(wallet_address, localconfig, TICKER_BLD)

    # Fetch count of transactions to estimate progress more accurately
    staketaxcsv.common.ibc.api_rpc_multinode.get_txs_pages_count(
        BLD_RPC_NODES, wallet_address, max_txs, progress, LIMIT_TXS_PER_QUERY)

    # Fetch transactions
    elems = staketaxcsv.common.ibc.api_rpc_multinode.get_txs_all(
        BLD_RPC_NODES, wallet_address, progress, max_txs, limit=LIMIT_TXS_PER_QUERY
    )

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.bld.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
