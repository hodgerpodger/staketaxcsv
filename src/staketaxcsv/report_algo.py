"""
usage: python3 report_algo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ALGO.<walletaddress>.<format>.csv
"""

import datetime
import json
import logging
import math
import os
import pprint

import staketaxcsv.algo.processor
from staketaxcsv.algo.api_algoindexer import LIMIT_ALGOINDEXER, AlgoIndexerAPI
from staketaxcsv.algo.api_nfdomains import NFDomainsAPI
from staketaxcsv.algo.asset import Asset
from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.algo.handle_algofi import (
    get_algofi_governance_rewards_transactions,
    get_algofi_liquidate_transactions,
    get_algofi_storage_address,
)
from staketaxcsv.algo.progress_algo import ProgressAlgo
from staketaxcsv.common import report_util
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import LP_TREATMENT_TRANSFERS
from staketaxcsv.settings_csv import REPORTS_DIR, TICKER_ALGO

indexer = AlgoIndexerAPI()


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_ALGO)

    if wallet_address.endswith(".algo"):
        wallet_address = NFDomainsAPI().get_address(wallet_address)

    report_util.run_report(TICKER_ALGO, wallet_address, export_format, txid, options)


def read_options(options):
    report_util.read_common_options(localconfig, options)

    localconfig.start_date = options.get("start_date", None)
    localconfig.end_date = options.get("end_date", None)
    localconfig.lp_treatment = options.get("lp_treatment", LP_TREATMENT_TRANSFERS)
    if "exclude_asas" in options:
        localconfig.exclude_asas = [asa.strip().lower() for asa in options["exclude_asas"].split(",")]
    localconfig.track_block = options.get("track_block", False)

    logging.info("localconfig: %s", localconfig.__dict__)


def _read_persistent_config(wallet_address):
    config_file = f"{REPORTS_DIR}/config.{TICKER_ALGO}.{wallet_address}.json"
    if localconfig.track_block and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            localconfig.min_round = config.get("min_round")
            logging.info(f"Starting from block {localconfig.min_round}")


def _write_persistent_config(wallet_address):
    if localconfig.track_block:
        config_file = f"{REPORTS_DIR}/config.{TICKER_ALGO}.{wallet_address}.json"
        with open(config_file, 'w') as f:
            config = {
                "min_round": localconfig.min_round
            }
            json.dump(config, f, indent=4)


def wallet_exists(wallet_address):
    return indexer.account_exists(wallet_address)


def txone(wallet_address, txid_or_groupid):
    progress = ProgressAlgo()

    elems = None
    data = indexer.get_transaction(txid_or_groupid)
    if data:
        if "group" in data:
            txid_or_groupid = data["group"]
        else:
            elems = [data]

    if elems is None:
        elems = indexer.get_transactions_by_group(txid_or_groupid)

    print("\ndebug data:")
    pprint.pprint(elems)
    print("")

    progress.set_estimate(1)
    exporter = Exporter(wallet_address, localconfig, TICKER_ALGO)
    staketaxcsv.algo.processor.process_txs(wallet_address, elems, exporter, progress)
    print("")

    return exporter


def _max_queries():
    max_txs = localconfig.limit
    max_queries = math.ceil(max_txs / LIMIT_ALGOINDEXER)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def txhistory(wallet_address, options):
    _read_persistent_config(wallet_address)

    progress = ProgressAlgo()
    exporter = Exporter(wallet_address, localconfig, TICKER_ALGO)

    account = indexer.get_account(wallet_address)
    if account is not None:
        Asset.load_assets(account.get("assets", []))

    # Retrieve data
    elems = _get_txs(wallet_address, account, progress)

    # Create rows for CSV
    staketaxcsv.algo.processor.process_txs(wallet_address, elems, exporter, progress)

    _write_persistent_config(wallet_address)

    # Log error stats if exists
    ErrorCounter.log(TICKER_ALGO, wallet_address)

    return exporter


def _get_txs(wallet_address, account, progress):
    # Debugging only: when --debug flag set, read from cache file
    debug_file = f"{REPORTS_DIR}/debug.{TICKER_ALGO}.{wallet_address}.json"
    if localconfig.debug and os.path.exists(debug_file):
        with open(debug_file, 'r') as f:
            out = json.load(f)
            return out

    out = _get_address_transactions(wallet_address)
    # Reverse the list so transactions are in chronological order
    out.reverse()
    if len(out) > 0:
        localconfig.min_round = out[-1]["confirmed-round"] + 1

    if account is not None:
        storage_address = get_algofi_storage_address(account)
        logging.debug("AlgoFi storage address: %s", storage_address)
        if storage_address is not None:
            localconfig.algofi_storage_address = storage_address
            storage_txs = _get_address_transactions(storage_address)
            out.extend(get_algofi_liquidate_transactions(storage_txs))
            out.extend(get_algofi_governance_rewards_transactions(storage_txs, storage_address))

    num_tx = len(out)

    progress.set_estimate(num_tx)
    message = "Retrieved total {} txids...".format(num_tx)
    progress.report_message(message)

    # Debugging only: when --debug flat set, write to cache file
    if localconfig.debug:
        with open(debug_file, 'w') as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", debug_file)

    return out


def _get_address_transactions(address):
    next = None
    out = []

    after_date = None
    before_date = None
    if localconfig.start_date:
        after_date = datetime.date.fromisoformat(localconfig.start_date)
    if localconfig.end_date:
        before_date = datetime.date.fromisoformat(localconfig.end_date) + datetime.timedelta(days=1)

    for _ in range(_max_queries()):
        transactions, next = indexer.get_transactions(
            address, after_date, before_date, localconfig.min_round, next)
        out.extend(transactions)

        if not next:
            break

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
