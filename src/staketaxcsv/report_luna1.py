"""
usage: python3 report_luna1.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/LUNA1*.csv


Notes:
    * Terra Classic
    * https://fcd.terra.dev/swagger
    * https://columbus-lcd.terra.dev/swagger/
"""

import json
import logging
import math
import os
import pprint

import staketaxcsv.luna1.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import FORMAT_DEFAULT, LP_TREATMENT_TRANSFERS
from staketaxcsv.luna1.api_fcd import LIMIT_FCD, FcdAPI
from staketaxcsv.luna1.api_lcd import LcdAPI
from staketaxcsv.luna1.config_luna1 import localconfig
from staketaxcsv.luna1.progress_terra import SECONDS_PER_TX_FETCH, SECONDS_PER_TX_PROCESS, ProgressTerra
from staketaxcsv.settings_csv import TICKER_LUNA1


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_LUNA1)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_LUNA1, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)

    localconfig.lp_treatment = options.get("lp_treatment", LP_TREATMENT_TRANSFERS)
    localconfig.minor_rewards = options.get("minor_rewards", False)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    if not wallet_address.startswith("terra"):
        return False

    return LcdAPI.has_txs(wallet_address)


def txone(wallet_address, txid):
    data = FcdAPI.get_tx(txid)
    print("\ndebug data:")
    pprint.pprint(data)
    print("")

    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA1)
    txinfo = staketaxcsv.luna1.processor.process_tx(wallet_address, data, exporter)
    txinfo.print()
    print("")

    return exporter


def estimate_duration(wallet_address, options):
    return (SECONDS_PER_TX_FETCH + SECONDS_PER_TX_PROCESS) * LcdAPI.num_txs(wallet_address)


def _max_queries():
    max_txs = localconfig.limit
    max_queries = math.ceil(max_txs / LIMIT_FCD)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        cache = Cache()
        _cache_load(cache)

    progress = ProgressTerra()
    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA1)

    num_txs = LcdAPI.num_txs(wallet_address)
    progress.set_estimate(num_txs)
    logging.info("num_txs=%s", num_txs)

    # Retrieve data
    elems = _get_txs(wallet_address, progress)
    elems.sort(key=lambda elem: elem["timestamp"])

    # Create rows for CSV
    staketaxcsv.luna1.processor.process_txs(wallet_address, elems, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_LUNA1, wallet_address)

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

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
