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
from common.ExporterTypes import FORMAT_DEFAULT, LP_TREATMENT_TRANSFERS
from settings_csv import TICKER_ALGO


def main():
    wallet_address, export_format, txid_or_groupid, options = report_util.parse_args(TICKER_ALGO)

    if txid_or_groupid:
        _read_options(options)
        exporter = txone(wallet_address, txid_or_groupid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid_or_groupid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_ALGO, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)

    localconfig.after_date = options.get("after_date", None)
    localconfig.before_date = options.get("before_date", None)
    localconfig.lp_treatment = options.get("lp_treatment", LP_TREATMENT_TRANSFERS)

    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return AlgoIndexerAPI.account_exists(wallet_address)


def txone(wallet_address, txid_or_groupid):
    progress = ProgressAlgo()

    data = AlgoIndexerAPI.get_transaction(txid_or_groupid)
    if data:
        elems = [data]
    else:
        elems = AlgoIndexerAPI.get_transactions_by_group(txid_or_groupid)

    print("\ndebug data:")
    pprint.pprint(elems)
    print("")

    progress.set_estimate(1)
    exporter = Exporter(wallet_address, localconfig, TICKER_ALGO)
    algo.processor.process_txs(wallet_address, elems, exporter, progress)
    print("")

    return exporter


def _max_queries():
    max_txs = localconfig.limit
    max_queries = math.ceil(max_txs / LIMIT_ALGOINDEXER)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)

    progress = ProgressAlgo()
    exporter = Exporter(wallet_address, localconfig, TICKER_ALGO)

    # Retrieve data
    elems = _get_txs(wallet_address, progress)

    # Create rows for CSV
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
        transactions, next = AlgoIndexerAPI.get_transactions(
            wallet_address, localconfig.after_date, localconfig.before_date, next)
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
