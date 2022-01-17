"""
usage: python3 report_terra.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/LUNA*.csv


Notes:
    * https://fcd.terra.dev/swagger
    * https://lcd.terra.dev/swagger/
    * https://docs.figment.io/network-documentation/terra/enriched-apis
"""

import json
import logging
import math
import os
import pprint

import terra.processor
from common import report_util
from common.Cache import Cache
from common.ErrorCounter import ErrorCounter
from common.Exporter import Exporter
from settings_csv import TERRA_FIGMENT_KEY, TICKER_LUNA
from terra.api_fcd import LIMIT_FCD, FcdAPI
from terra.api_search_figment import LIMIT_FIGMENT, SearchAPIFigment
from terra.config_terra import localconfig
from terra.ProgressTerra import SECONDS_PER_TX, ProgressTerra

MAX_TRANSACTIONS = 10000


def main():
    wallet_address, format, txid, options = report_util.parse_args()
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address, job=None)
        report_util.run_exports(TICKER_LUNA, wallet_address, exporter, format)


def _read_options(options):
    if options:
        # Check for options with non-default values
        if options.get("debug") is True:
            localconfig.debug = True
        if options.get("cache") is True:
            localconfig.cache = True
        if options.get("minor_rewards") is True:
            localconfig.minor_rewards = True
        if options.get("lp") is True:
            localconfig.lp = True
        if options.get("limit"):
            localconfig.limit = options.get("limit")


def wallet_exists(wallet_address):
    if not wallet_address.startswith("terra"):
        return False
    data = SearchAPIFigment.get_txs(wallet_address, limit=2)
    if data is None:
        return False
    return len(data) > 0


def txone(wallet_address, txid):
    data = FcdAPI.get_tx(txid)
    print("\ndebug data:")
    pprint.pprint(data)
    print("")

    exporter = Exporter(wallet_address)
    terra.processor.process_tx(wallet_address, data, exporter)
    print("")
    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_TX * _num_txs(wallet_address)


def _max_queries():
    max_txs = localconfig.limit if localconfig.limit else MAX_TRANSACTIONS
    max_queries = math.ceil(max_txs / LIMIT_FCD)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def _num_txs(wallet_address):
    num_txs = 0
    for _ in range(_max_queries()):
        logging.info("estimate_duration() loop num_txs=%s", num_txs)

        data = SearchAPIFigment.get_txs(wallet_address, offset=num_txs)
        num_txs += len(data)

        if len(data) < LIMIT_FIGMENT:
            break

    return num_txs


def txhistory(wallet_address, job=None, options=None):
    progress = ProgressTerra()

    if options:
        _read_options(options)
    if job:
        localconfig.job = job
        localconfig.cache = True
    if localconfig.cache:
        localconfig.currency_addresses = Cache().get_terra_currency_addresses()
        logging.info("Loaded terra_currency_addresses from cache ...")
    if TERRA_FIGMENT_KEY:
        # Optional: Fetch count of transactions to estimate progress more accurately later
        num_txs = _num_txs(wallet_address)
        progress.set_estimate(num_txs)
        logging.info("num_txs=%s", num_txs)

    # Retrieve data
    elems = _get_txs(wallet_address, progress, num_txs)
    elems.sort(key=lambda elem: elem["timestamp"])

    # Create rows for CSV
    exporter = Exporter(wallet_address)
    terra.processor.process_txs(wallet_address, elems, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_LUNA, wallet_address)

    if localconfig.cache:
        Cache().set_terra_currency_addresses(localconfig.currency_addresses)
    return exporter


def _get_txs(wallet_address, progress, total_txs):
    # Debugging only: when --debug flag set, read from cache file
    if localconfig.debug:
        debug_file = f"_reports/debugterra.{wallet_address}.json"
        if os.path.exists(debug_file):
            with open(debug_file, "r") as f:
                out = json.load(f)
                return out

    offset = 0
    out = []
    for _ in range(_max_queries()):
        num_tx = len(out)
        progress.report(num_tx, f"Retrieving transaction {num_tx + 1} of {total_txs} ...")

        data = FcdAPI.get_txs(wallet_address, offset)
        result = data["txs"]
        out.extend(result)

        if len(result) == LIMIT_FCD and "next" in data:
            offset = data["next"]
        else:
            break

    message = f"Retrieved total {len(out)} txids..."
    progress.report_message(message)

    # Debugging only: when --debug flat set, write to cache file
    if localconfig.debug:
        with open(debug_file, "w") as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", debug_file)

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
