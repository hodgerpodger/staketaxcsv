"""
usage: python3 report_algo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ALGO.<walletaddress>.<format>.csv
"""

import json
import logging
import math
import os
import pprint

import algo.processor
from algo.api_algoindexer import LIMIT_ALGOINDEXER, AlgoIndexerAPI
from algo.config_algo import localconfig
from algo.progress_algo import ProgressAlgo
from common import report_util
from common.ErrorCounter import ErrorCounter
from common.Exporter import Exporter
from settings_csv import TICKER_ALGO

MAX_TRANSACTIONS = 10000


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_ALGO)
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address)
        report_util.run_exports(TICKER_ALGO, wallet_address, exporter, export_format)


def _read_options(options):
    if options:
        # Check for options with non-default values
        if options.get("debug") is True:
            localconfig.debug = True
        if options.get("cache") is True:
            localconfig.cache = True
        if options.get("limit"):
            localconfig.limit = options.get("limit")


def wallet_exists(wallet_address):
    return AlgoIndexerAPI.account_exists(wallet_address)


def txone(wallet_address, txid):
    progress = ProgressAlgo()

    data = AlgoIndexerAPI.get_transaction(txid)
    print("\ndebug data:")
    pprint.pprint(data)
    print("")

    progress.set_estimate(1)
    exporter = Exporter(wallet_address)
    algo.processor.process_txs(wallet_address, [data], exporter, progress)
    print("")

    return exporter


def _max_queries():
    max_txs = localconfig.limit if localconfig.limit else MAX_TRANSACTIONS
    max_queries = math.ceil(max_txs / LIMIT_ALGOINDEXER)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def txhistory(wallet_address):
    progress = ProgressAlgo()

    # Retrieve data
    elems = _get_txs(wallet_address, progress)

    # Create rows for CSV
    exporter = Exporter(wallet_address)
    algo.processor.process_txs(wallet_address, elems, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_ALGO, wallet_address)

    return exporter


def _get_txs(wallet_address, progress):
    # Debugging only: when --debug flag set, read from cache file
    DEBUG_FILE = "_reports/debugalgo.{}.json".format(wallet_address)
    if localconfig.debug and os.path.exists(DEBUG_FILE):
        with open(DEBUG_FILE, 'r') as f:
            out = json.load(f)
            return out

    next = None
    out = []
    for i in range(_max_queries()):
        transactions, next = AlgoIndexerAPI.get_transactions(wallet_address, next)
        out.extend(transactions)

        if not next:
            break

    num_tx = len(out)
    progress.set_estimate(num_tx)
    message = "Retrieved total {} txids...".format(num_tx)
    progress.report_message(message)

    # Reverse the list so transactions are in chronological order
    out.reverse()

    # Debugging only: when --debug flat set, write to cache file
    if localconfig.debug:
        with open(DEBUG_FILE, 'w') as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", DEBUG_FILE)

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
