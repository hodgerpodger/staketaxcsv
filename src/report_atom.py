"""
usage: python3 report_atom.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ATOM*.csv


Notes:

https://node.atomscan.com/swagger/

"""

import json
import logging
import math
import os
import pprint

import atom.api_cosmostation
import atom.api_lcd
import atom.processor
from atom.config_atom import localconfig
from atom.progress_atom import SECONDS_PER_PAGE, ProgressAtom
from common import report_util
from common.Cache import Cache
from common.Exporter import Exporter
from common.ExporterTypes import FORMAT_DEFAULT
from settings_csv import TICKER_ATOM

LIMIT_PER_QUERY = 50


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_ATOM)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_ATOM, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)

    localconfig.legacy = options.get("legacy", False)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return atom.api_lcd.account_exists(wallet_address)


def txone(wallet_address, txid):
    if localconfig.legacy:
        elem = atom.api_cosmostation.get_tx(txid)
    else:
        elem = atom.api_lcd.get_tx(txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_ATOM)
    atom.processor.process_tx(wallet_address, elem, exporter)
    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * atom.api_lcd.get_txs_count_pages(wallet_address)


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    progress = ProgressAtom()
    exporter = Exporter(wallet_address, localconfig, TICKER_ATOM)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = atom.api_lcd.get_txs_count_pages(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch legacy transactions conditionally (cosmoshub-3)
    elems = []
    if localconfig.legacy:
        elems.extend(_fetch_txs_legacy(wallet_address, progress))

    # Fetch transactions
    elems.extend(_fetch_txs(wallet_address, progress, count_pages))
    elems = _remove_duplicates(elems)

    progress.report_message(f"Processing {len(elems)} ATOM transactions... ")
    atom.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


def _max_pages():
    max_txs = localconfig.limit
    max_pages = math.ceil(max_txs / LIMIT_PER_QUERY)
    logging.info("max_txs: %s, max_pages: %s", max_txs, max_pages)
    return max_pages


def _fetch_txs_legacy(wallet_address, progress):
    out = []
    next_id = None
    current_page = 0

    for _ in range(0, _max_pages()):
        message = f"Fetching page {current_page} for legacy transactions ..."
        progress.report_message(message)
        current_page += 1

        elems, next_id = atom.api_cosmostation.get_txs_legacy(wallet_address, next_id)
        out.extend(elems)
        if next_id is None:
            break

    return out


def _fetch_txs(wallet_address, progress, num_pages):
    if localconfig.debug:
        debug_file = f"_reports/testatom.{wallet_address}.json"
        if os.path.exists(debug_file):
            with open(debug_file, "r") as f:
                return json.load(f)

    out = []
    current_page = 0
    # Two passes: is_sender=True (message.sender events) and is_sender=False (transfer.recipient events)
    for is_sender in (True, False):
        offset = 0
        for _ in range(0, _max_pages()):
            message = f"Fetching page {current_page + 1} of {num_pages}"
            progress.report(current_page, message)
            current_page += 1

            elems, offset, _ = atom.api_lcd.get_txs(wallet_address, is_sender, offset)

            out.extend(elems)
            if offset is None:
                break

    # Debugging only
    if localconfig.debug:
        with open(debug_file, "w") as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", debug_file)
    return out


def _remove_duplicates(elems):
    out = []
    txids = set()

    for elem in elems:
        if elem["txhash"] in txids:
            continue

        out.append(elem)
        txids.add(elem["txhash"])

    out.sort(key=lambda elem: elem["timestamp"], reverse=True)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
