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
from osmo.progress_osmo import SECONDS_PER_PAGE, ProgressOsmo
from settings_csv import TICKER_OSMO

MAX_TRANSACTIONS = 5000


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_OSMO)
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address, job=None)
        report_util.run_exports(TICKER_OSMO, wallet_address, exporter, export_format)


def _read_options(options):
    if not options:
        return

    localconfig.debug = options.get("debug", False)
    localconfig.cache = options.get("cache", False)
    localconfig.limit = options.get("limit", None)
    localconfig.lp_transfers = options.get("lp_transfers", False)
    localconfig.lp_trades = options.get("lp_trades", False)


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
    num_pages = len(_pages(wallet_address))
    return num_pages * SECONDS_PER_PAGE


def _pages(wallet_address):
    """ Returns list of page numbers to be retrieved """
    max_txs = localconfig.limit if localconfig.limit else MAX_TRANSACTIONS
    num_txs = min(osmo.api_data.get_count_txs(wallet_address), max_txs)

    last_page = math.ceil(num_txs / osmo.api_data.LIMIT_PER_QUERY) - 1
    pages = list(range(last_page, -1, -1))
    return pages


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

    # Set time estimate to estimate progress later
    reward_tokens = osmo.api_data.get_lp_tokens(wallet_address)
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

        elems = osmo.api_data.get_txs(wallet_address, page * osmo.api_data.LIMIT_PER_QUERY)

        # Remove duplicates (data from this api has duplicates)
        elems_clean = _remove_dups(elems, txids_seen)

        # Sort to process oldest first (so that lock/unlock tokens transactions processed correctly)
        elems_clean.sort(key=lambda elem: elem["timestamp"])

        osmo.processor.process_txs(wallet_address, elems_clean, exporter)
        count_txs_processed += len(elems)

    # Report final progress
    progress.report(i, f"Retrieved total {count_txs_processed} transactions...", "txs")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
