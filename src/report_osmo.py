"""
usage: python3 report_osmo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/OSMO*.csv

"""

import logging
import math
import pprint

import osmo.api_data
import osmo.api_tx
import osmo.processor
from common import report_util
from common.Cache import Cache
from common.ErrorCounter import ErrorCounter
from common.Exporter import Exporter
from osmo.config_osmo import localconfig
from osmo.lp_rewards import lp_rewards
from osmo.progress_osmo import SECONDS_PER_TX, ProgressOsmo
from settings_csv import TICKER_OSMO

MAX_TRANSACTIONS = 5000


def main():
    wallet_address, export_format, txid, options = report_util.parse_args()
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address, job=None)
        report_util.run_exports(TICKER_OSMO, wallet_address, exporter, export_format)


def _read_options(options):
    if options:
        # Check for options with non-default values
        if options.get("debug") is True:
            localconfig.debug = True
        if options.get("limit"):
            localconfig.limit = options.get("limit")
        if options.get("lp") is True:
            localconfig.lp = True
        if options.get("cache") is True:
            localconfig.cache = True


def wallet_exists(wallet_address):
    if not wallet_address.startswith("osmo"):
        return False
    count = osmo.api_data.get_count_txs(wallet_address)
    return count > 0


def txone(wallet_address, txid):
    data = osmo.api_tx.get_tx(txid)
    print("\ndebug data:")
    pprint.pprint(data)
    print("\n")

    exporter = Exporter(wallet_address)
    txinfo = osmo.processor.process_tx(wallet_address, data, exporter)
    txinfo.print()

    return exporter


def estimate_duration(wallet_address):
    return osmo.api_data.get_count_txs(wallet_address, sleep_seconds=0) * SECONDS_PER_TX


def txhistory(wallet_address, job=None, options=None):
    exporter = Exporter(wallet_address)
    progress = ProgressOsmo()

    if options:
        _read_options(options)
    if job:
        localconfig.job = job
        localconfig.cache = True
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_osmo_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    # Estimate total time to create CSV
    reward_tokens = osmo.api_data.get_lp_tokens(wallet_address)

    num_txs = min(osmo.api_data.get_count_txs(wallet_address), MAX_TRANSACTIONS)
    progress.set_estimate(num_txs, len(reward_tokens))
    logging.info("num_txs: %s", num_txs)

    # Transactions data
    _fetch_and_process_txs(wallet_address, exporter, progress, num_txs)

    # LP rewards data
    lp_rewards(wallet_address, reward_tokens, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_OSMO, wallet_address)

    if localconfig.cache:
        # Remove entries where no symbol was found
        localconfig.ibc_addresses = {k: v for k, v in localconfig.ibc_addresses.items() if not v.startswith("ibc/")}
        Cache().set_osmo_ibc_addresses(localconfig.ibc_addresses)
    return exporter


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


def _fetch_and_process_txs(wallet_address, exporter, progress, num_txs):
    # Predetermine pages to retrieve
    last_page = math.ceil(num_txs / osmo.api_data.LIMIT) - 1
    pages = range(last_page, -1, -1)

    # Fetch and parse data in batches (cumulative required too much memory), oldest first.
    # Note: oldest first is opposite of api default (allows simpler lp stake/unstake logic)
    count_txs_processed = 0
    txids_seen = set()
    for page in pages:
        message = f"Fetching txs page={page} for range [0, {last_page}]"
        progress.report(count_txs_processed, message, "txs")

        elems = osmo.api_data.get_txs(wallet_address, page * osmo.api_data.LIMIT)

        # Remove duplicates (data from this api has duplicates)
        elems_clean = _remove_dups(elems, txids_seen)

        # Sort to process oldest first (so that lock/unlock tokens transactions processed correctly)
        elems_clean.sort(key=lambda elem: elem["timestamp"])

        osmo.processor.process_txs(wallet_address, elems_clean, exporter)
        count_txs_processed += len(elems)

    # Report final progress
    progress.report(num_txs, f"Retrieved all {num_txs} transactions...", "txs")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
