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
from common.ExporterTypes import FORMAT_DEFAULT, LP_TREATMENT_TRANSFERS
from settings_csv import TERRA_FIGMENT_KEY, TICKER_LUNA
from terra.api_fcd import LIMIT_FCD, FcdAPI
from terra.api_search_figment import LIMIT_FIGMENT, SearchAPIFigment
from terra.config_terra import localconfig
from terra.progress_terra import SECONDS_PER_TX, ProgressTerra


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_LUNA)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_LUNA, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)

    localconfig.lp_treatment = options.get("lp_treatment", LP_TREATMENT_TRANSFERS)
    localconfig.minor_rewards = options.get("minor_rewards", False)
    logging.info("localconfig: %s", localconfig.__dict__)


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

    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA)
    terra.processor.process_tx(wallet_address, data, exporter)
    print("")
    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_TX * _num_txs(wallet_address)


def _max_queries():
    max_txs = localconfig.limit
    max_queries = math.ceil(max_txs / LIMIT_FCD)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def _num_txs(wallet_address):
    num_txs = 0
    figment_max_queries = math.ceil(localconfig.limit / LIMIT_FIGMENT)

    for _ in range(figment_max_queries):
        logging.info("estimate_duration() loop num_txs=%s", num_txs)

        data = SearchAPIFigment.get_txs(wallet_address, offset=num_txs)
        num_txs += len(data)

        if len(data) < LIMIT_FIGMENT:
            break

    return num_txs


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        cache = Cache()
        _cache_load(cache)

    progress = ProgressTerra()
    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA)

    if TERRA_FIGMENT_KEY:
        # Optional: Fetch count of transactions to estimate progress more accurately later
        num_txs = _num_txs(wallet_address)
        progress.set_estimate(num_txs)
        logging.info("num_txs=%s", num_txs)

    # Retrieve data
    elems = _get_txs(wallet_address, progress)
    elems.sort(key=lambda elem: elem["timestamp"])

    # Create rows for CSV
    terra.processor.process_txs(wallet_address, elems, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_LUNA, wallet_address)

    if localconfig.cache:
        _cache_push(cache)
    return exporter


def _cache_load(cache):
    localconfig.ibc_addresses = cache.get_ibc_addresses()
    localconfig.currency_addresses = cache.get_terra_currency_addresses()
    localconfig.decimals = cache.get_terra_decimals()
    localconfig.lp_currency_addresses = cache.get_terra_lp_currency_addresses()

    logging.info("_cache_load(): downloaded data from cache ...")


def _cache_push(cache):
    cache.set_ibc_addresses(localconfig.ibc_addresses)
    cache.set_terra_currency_addresses(localconfig.currency_addresses)
    cache.set_terra_decimals(localconfig.decimals)
    cache.set_terra_lp_currency_addresses(localconfig.lp_currency_addresses)

    logging.info("_cache_push(): push data to cache")


def _get_txs(wallet_address, progress):
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
        progress.report(num_tx, f"Retrieving transaction {num_tx + 1} ...")

        data = FcdAPI.get_txs(wallet_address, offset)
        result = data["txs"]
        out.extend(result)

        if data.get("next", None):
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
