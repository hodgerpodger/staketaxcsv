"""
usage: python3 report_osmo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/OSMO*.csv

"""

import logging
import math
import pprint

import staketaxcsv.osmo.api_data
import staketaxcsv.osmo.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import FORMAT_DEFAULT, LP_TREATMENT_TRANSFERS
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo.lp_rewards import lp_rewards
from staketaxcsv.osmo.progress_osmo import SECONDS_PER_PAGE, ProgressOsmo
from staketaxcsv.settings_csv import TICKER_OSMO


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_OSMO)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_OSMO, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)

    localconfig.lp_treatment = options.get("lp_treatment", LP_TREATMENT_TRANSFERS)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    if not wallet_address.startswith("osmo"):
        return False
    count = staketaxcsv.osmo.api_data.get_count_txs(wallet_address)
    return count > 0


def txone(wallet_address, txid):
    data = staketaxcsv.osmo.api_data.get_tx(txid)
    print("\ndebug data:")
    pprint.pprint(data)
    print("\n")

    exporter = Exporter(wallet_address, localconfig, TICKER_OSMO)
    txinfo = staketaxcsv.osmo.processor.process_tx(wallet_address, data, exporter)
    txinfo.print()

    return exporter


def estimate_duration(wallet_address, options):
    num_pages = len(_pages(wallet_address))
    return num_pages * SECONDS_PER_PAGE


def _pages(wallet_address):
    """ Returns list of page numbers to be retrieved """
    max_txs = localconfig.limit
    num_txs = min(staketaxcsv.osmo.api_data.get_count_txs(wallet_address), max_txs)

    last_page = math.ceil(num_txs / staketaxcsv.osmo.api_data.LIMIT_PER_QUERY) - 1
    pages = list(range(last_page, -1, -1))
    return pages


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        cache = Cache()
        _cache_load(cache)

    progress = ProgressOsmo()
    exporter = Exporter(wallet_address, localconfig, TICKER_OSMO)

    # Set time estimate to estimate progress later
    reward_tokens = staketaxcsv.osmo.api_data.get_lp_tokens(wallet_address)
    pages = _pages(wallet_address)
    progress.set_estimate(len(pages), len(reward_tokens))
    logging.info("pages: %s, reward_tokens: %s", pages, reward_tokens)

    # Transactions data
    _fetch_and_process_txs(wallet_address, exporter, progress, pages)

    # LP rewards data
    lp_rewards(wallet_address, reward_tokens, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_OSMO, wallet_address)

    if localconfig.cache:
        _cache_push(cache)
    return exporter


def _cache_load(cache):
    localconfig.ibc_addresses = cache.get_ibc_addresses()
    localconfig.exponents = cache.get_osmo_exponents()

    logging.info("_cache_load(): downloaded data from cache ...")


def _cache_push(cache):
    cache.set_ibc_addresses(localconfig.ibc_addresses)
    cache.set_osmo_exponents(localconfig.exponents)

    logging.info("_cache_push(): push data to cache")


def _remove_dups(elems, txids_seen):
    """API data has duplicate transaction data.  Clean it."""
    out = []
    for elem in elems:
        txid = elem["txhash"]
        if txid in txids_seen:
            continue

        out.append(elem)
        txids_seen.add(txid)

    return out


def _fetch_and_process_txs(wallet_address, exporter, progress, pages):
    # Fetch and parse data in batches (cumulative required too much memory), oldest first.
    # Note: oldest first is opposite of api default (allows simpler lp stake/unstake logic)
    count_txs_processed = 0
    txids_seen = set()
    i = 0
    for page in pages:
        message = "Fetching txs page={} in range [0,{}]".format(page, pages[0])
        progress.report(i, message, "txs")
        i += 1

        elems = staketaxcsv.osmo.api_data.get_txs(wallet_address, page * staketaxcsv.osmo.api_data.LIMIT_PER_QUERY)

        # Remove duplicates (data from this api has duplicates)
        elems_clean = _remove_dups(elems, txids_seen)

        # Sort to process oldest first (so that lock/unlock tokens transactions processed correctly)
        elems_clean.sort(key=lambda elem: elem["timestamp"])

        staketaxcsv.osmo.processor.process_txs(wallet_address, elems_clean, exporter)
        count_txs_processed += len(elems)

    # Report final progress
    progress.report(i, f"Retrieved total {count_txs_processed} transactions...", "txs")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
