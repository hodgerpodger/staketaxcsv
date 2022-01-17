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
import subprocess

import atom.api_lcd
import atom.processor
from atom.config_atom import localconfig
from atom.progress_atom import ProgressAtom
from common import report_util
from common.Exporter import Exporter
from settings_csv import TICKER_ATOM

LIMIT = 50
MAX_TRANSACTIONS = 1000


def _cmd(s):
    logging.info(s)
    return subprocess.getoutput(s)


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
    if options:
        if options.get("debug") is True:
            localconfig.debug = True
        if options.get("limit"):
            localconfig.limit = options.get("limit")


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
    count_pages = atom.api_lcd.get_txs_count_pages(wallet_address)
    logging.info("count_pages: %s", count_pages)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = _fetch_txs(wallet_address, progress, count_pages)
    progress.report_message(f"Processing {len(elems)} ATOM transactions... ")

    exporter = Exporter(wallet_address)
    atom.processor.process_txs(wallet_address, elems, exporter)

    return exporter


def _max_pages():
    max_txs = localconfig.limit if localconfig.limit else MAX_TRANSACTIONS
    max_pages = math.ceil(max_txs / LIMIT)
    logging.info("max_txs: %s, max_pages: %s", max_txs, max_pages)
    return max_pages


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
            current_page += 1
            message = f"Fetching page {current_page} of {num_pages}"
            progress.report(current_page, message)

            elems, offset, _ = atom.api_lcd.get_txs(wallet_address, is_sender, offset)

            out.extend(elems)
            if offset is None:
                break

    out = _remove_duplicates(out)

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
