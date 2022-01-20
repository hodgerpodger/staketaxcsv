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

import atom.api_lcd
import atom.processor
from atom.config_atom import localconfig
from atom.progress_atom import ProgressAtom
from common import report_util
from common.Exporter import Exporter
from settings_csv import TICKER_ATOM

LIMIT = 50
MAX_TRANSACTIONS = 1000


def main():
    wallet_address, export_format, txid, options = report_util.parse_args()
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address)
        report_util.run_exports(TICKER_ATOM, wallet_address, exporter, export_format)


def _read_options(options):
    if not options:
        return

    localconfig.debug = options.get("debug", False)
    localconfig.limit = options.get("limit", None)


def wallet_exists(wallet_address):
    return atom.api_lcd.account_exists(wallet_address)


def txone(wallet_address, txid):
    data = atom.api_lcd.get_tx(txid)

    print("Transaction data:")
    pprint.pprint(data)

    exporter = Exporter(wallet_address)
    atom.processor.process_tx(wallet_address, data, exporter)
    return exporter


def txhistory(wallet_address, job=None):
    if job:
        localconfig.job = job

    # Fetch count of transactions to estimate progress more accurately
    progress = ProgressAtom()
    sender_page_count, receiver_page_count = atom.api_lcd.get_txs_count_pages(wallet_address)

    # Fetch transactions
    elems = _fetch_txs(wallet_address, progress, sender_page_count, receiver_page_count)
    progress.report_message(f"Processing {len(elems)} ATOM transactions... ")

    exporter = Exporter(wallet_address)
    atom.processor.process_txs(wallet_address, elems, exporter)

    return exporter


def _max_pages():
    max_txs = localconfig.limit if localconfig.limit is not None else MAX_TRANSACTIONS
    max_pages = math.ceil(max_txs / LIMIT)
    logging.info("max_txs: %s, max_pages: %s", max_txs, max_pages)
    return max_pages


def _fetch_txs(wallet_address, progress, sender_page_count, receiver_page_count):
    if localconfig.debug:
        debug_file = f"_reports/testatom.{wallet_address}.json"
        if os.path.exists(debug_file):
            with open(debug_file, "r") as f:
                return json.load(f)

    page_limit = _max_pages()
    sender_page_limit = min(sender_page_count, page_limit)
    receiver_page_limit = min(receiver_page_count, page_limit)

    progress.set_estimate(sender_page_limit, receiver_page_limit)

    out = []
    seen_txids = set()

    message = f"Fetching sender txs. {sender_page_limit} pages..."
    progress.report(0, message, "sender")

    sender_offset = 0
    for current_page in range(1, sender_page_limit + 1):
        elems, sender_offset, _ = atom.api_lcd.get_txs(wallet_address, True, sender_offset)
        _add_unseen_transaction(out, seen_txids, elems)

        message = f"Fetched sender txs page {current_page} of {sender_page_limit}"
        progress.report(current_page, message, "sender")

    # Sender txs fetching completed, report if results are truncated
    if sender_page_limit < sender_page_count:
        progress.report_message(
            f"Sender tx fetching stopped at {sender_page_limit} of possible {sender_page_count} pages..."
        )

    message = f"Fetching receiver txs. {receiver_page_limit} pages..."
    progress.report(0, message, "receiver")

    receiver_offset = 0
    for current_page in range(1, receiver_page_limit + 1):
        elems, receiver_offset, _ = atom.api_lcd.get_txs(wallet_address, False, receiver_offset)
        _add_unseen_transaction(out, seen_txids, elems)

        message = f"Fetched receiver txs page {current_page} of {receiver_page_limit}"
        progress.report(current_page, message, "receiver")

    # Receiver txs fetching completed, report if results are truncated
    if receiver_page_limit < receiver_page_count:
        progress.report_message(
            f"Receiver tx fetching stopped at {receiver_page_limit} of possible {receiver_page_count} pages..."
        )

    out.sort(key=lambda elem: elem["timestamp"], reverse=True)

    # Debugging only
    if localconfig.debug:
        with open(debug_file, "w") as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", debug_file)
    return out


def _add_unseen_transaction(out, seen_txids, elems):
    for elem in elems:
        if elem["txhash"] in seen_txids:
            continue

        out.append(elem)
        seen_txids.add(elem["txhash"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
