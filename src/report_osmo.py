
"""
usage: python3 report_osmo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/OSMO*.csv

"""

import logging
import json
import os
import pprint
import math
import osmo.api_data

from settings_csv import TICKER_OSMO
from common.Exporter import Exporter
from common.ErrorCounter import ErrorCounter
from common.Cache import Cache
from common import report_util
from osmo.config_osmo import localconfig
from osmo.ProgressOsmo import ProgressOsmo, SECONDS_PER_TX
from osmo.lp_rewards import lp_rewards
import osmo.processor
import osmo.api_data
import osmo.api_tx
MAX_TRANSACTIONS = 5000


def main():
    wallet_address, format, txid, options = report_util.parse_args()
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address, job=None)
        report_util.run_exports(TICKER_OSMO, wallet_address, exporter, format)


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
    return osmo.api_data.get_count_txs(wallet_address) * SECONDS_PER_TX


def _max_pages():
    max_txs = localconfig.limit if localconfig.limit else MAX_TRANSACTIONS
    max_pages = math.ceil(max_txs / osmo.api_data.LIMIT)
    logging.info("max_txs: %s, max_pages: %s", max_txs, max_pages)
    return max_pages


def txhistory(wallet_address, job=None, options=None):
    exporter = Exporter(wallet_address)

    if options:
        _read_options(options)
    if job:
        localconfig.job = job
        localconfig.cache = True
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_osmo_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    # Estimate total time to create CSV
    progress = ProgressOsmo()
    reward_tokens = osmo.api_data.get_lp_tokens(wallet_address)
    num_txs = min(osmo.api_data.get_count_txs(wallet_address), MAX_TRANSACTIONS)
    progress.set_estimate(num_txs, len(reward_tokens))

    # Transactions data
    _fetch_and_process_txs(wallet_address, exporter, progress)

    # LP rewards data
    lp_rewards(wallet_address, reward_tokens, exporter, progress)

    # Log error stats if exists
    ErrorCounter.log(TICKER_OSMO, wallet_address)

    if localconfig.cache:
        # Remove entries where no symbol was found
        localconfig.ibc_addresses = {k: v for k, v in localconfig.ibc_addresses.items()
                                     if not v.startswith("ibc/")}
        Cache().set_osmo_ibc_addresses(localconfig.ibc_addresses)
    return exporter


def _remove_dups(elems):
    """ API data has duplicate transaction data.  Clean it. """
    out = []
    txids_seen = set()
    for elem in elems:
        txid = elem["txhash"]
        if txid in txids_seen:
            continue

        out.append(elem)
        txids_seen.add(txid)

    # out.sort(key=lambda elem: elem["timestamp"])
    return out


def _fetch_and_process_txs(wallet_address, exporter, progress):
    pages_total_estimate = math.ceil(progress.num_txs / osmo.api_data.LIMIT)

    # Fetch and parse data in batches (Cumulative required too much memory)
    out = []
    for i in range(_max_pages()):
        message = "Fetching txs page {} of {}...".format(i, pages_total_estimate)
        progress.report(_fetch_and_process_txs.__name__, len(out), message)

        elems = osmo.api_data.get_txs(wallet_address, i * osmo.api_data.LIMIT)
        elems_clean = _remove_dups(elems)
        osmo.processor.process_txs(wallet_address, elems_clean, exporter)

        # Exit early if length of data indicates no more txs.
        if len(elems) != osmo.api_data.LIMIT:
            break

    # Report final progress
    progress.report_message("Retrieved total {} txids...".format(len(out)))

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
