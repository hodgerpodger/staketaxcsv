"""
usage: python3 report_algo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ALGO.<walletaddress>.<format>.csv
"""

import json
import logging
import math
import os
import pprint
from algo.asset import Asset
from algo.handle_algofi import get_algofi_storage_address

import algo.processor
from algo.api_algoindexer import LIMIT_ALGOINDEXER, AlgoIndexerAPI
from algo.config_algo import localconfig
from algo.progress_algo import ProgressAlgo
from common import report_util
from common.ErrorCounter import ErrorCounter
from common.Exporter import Exporter
from common.ExporterTypes import FORMAT_DEFAULT, LP_TREATMENT_TRANSFERS
from settings_csv import TICKER_ALGO

indexer = AlgoIndexerAPI()


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
    return indexer.account_exists(wallet_address)


def txone(wallet_address, txid_or_groupid):
    progress = ProgressAlgo()

    data = indexer.get_transaction(txid_or_groupid)
    if data:
        elems = [data]
    else:
        elems = indexer.get_transactions_by_group(txid_or_groupid)

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

    account = indexer.get_account(wallet_address)
    Asset.load_assets(account.get("assets", []))

    # Retrieve data
    elems = _get_txs(wallet_address, account, progress)

    # Create rows for CSV
    algo.processor.process_txs(wallet_address, elems, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_ALGO, wallet_address)

    return exporter


def _get_txs(wallet_address, account, progress):
    # Debugging only: when --debug flag set, read from cache file
    DEBUG_FILE = "_reports/debugalgo.{}.json".format(wallet_address)
    if localconfig.debug and os.path.exists(DEBUG_FILE):
        with open(DEBUG_FILE, 'r') as f:
            out = json.load(f)
            return out

    out = _get_address_transactions(wallet_address)
    # Reverse the list so transactions are in chronological order
    out.reverse()

    storage_address = get_algofi_storage_address(account)
    logging.debug("AlgoFi storage address: %s", storage_address)
    storage_txs = _get_address_transactions(storage_address)
    out.extend([tx for tx in storage_txs if "inner-txns" in tx])

    num_tx = len(out)

    progress.set_estimate(num_tx)
    message = "Retrieved total {} txids...".format(num_tx)
    progress.report_message(message)

    # Debugging only: when --debug flat set, write to cache file
    if localconfig.debug:
        with open(DEBUG_FILE, 'w') as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", DEBUG_FILE)

    return out


def _get_address_transactions(address):
    next = None
    out = []
    for i in range(_max_queries()):
        transactions, next = indexer.get_transactions(
            address, localconfig.after_date, localconfig.before_date, next)
        out.extend(transactions)

        if not next:
            break

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
