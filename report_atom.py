
"""
usage: python3 report_atom.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ATOM*.csv


Notes:

gaiad query txs --home /tmp/.gaia --events message.sender=cosmos1p4ks5aktxq48yqmpzh8e90z6suan8zwy463ypu \
      --node https://<RPCURL>:443 --limit 100

gaiad query txs --home /tmp/.gaia --events transfer.recipient=cosmos1p4ks5aktxq48yqmpzh8e90z6suan8zwy463ypu \
      --node https://<RPCURL>:443 --limit 100

 * The "--home /tmp/.gaia" is required for aws lambda

"""

from json.decoder import JSONDecodeError
import logging
import subprocess
import json
import os
import pprint
import time

from common import report_util
from common.Exporter import Exporter
import atom.processor
from atom.config_atom import localconfig
from settings_csv import TICKER_ATOM, ATOM_NODE
from atom.ProgressAtom import ProgressAtom

LIMIT = 50   # Cannot go more than 100 per query
MAX_TRANSACTIONS = 1000
MAX_PAGES = int(MAX_TRANSACTIONS / LIMIT)
CHAIN_IDS = ["cosmoshub-4"]

# Required for aws lambda
HOME = "/tmp/.gaia"


def _cmd(s):
    logging.info(s)
    return subprocess.getoutput(s)


def main():
    wallet_address, format, txid, options = report_util.parse_args()
    readOptions(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address)
        report_util.run_exports(TICKER_ATOM, wallet_address, exporter, format)


def readOptions(options):
    if options:
        if options.get("debug") is True:
            localconfig.debug = True


def wallet_exists(wallet_address):
    line = "gaiad query account {} --home {} --node {} --output json".format(wallet_address, HOME, ATOM_NODE)
    output_string = _cmd(line)
    logging.info("json_string: %s", output_string)

    if "pub_key" in output_string:
        return True
    else:
        return False


def txone(wallet_address, txid):
    line = "gaiad query tx {} --home {} --node={} ".format(txid, HOME, ATOM_NODE)
    line += "| python -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin, Loader=yaml.FullLoader), sys.stdout, indent=4)'"
    json_string = _cmd(line)
    data = json.loads(json_string)

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
    progress.report_message("Fetching counts...")
    pages = _count_txs(wallet_address)
    progress.set_estimate(pages)
    logging.info("num_pages:%s, pages: %s", len(pages), pages)

    # Fetch transactions
    elems = _fetch_txs(wallet_address, pages, progress)
    progress.report_message("Processing {} ATOM transactions... ".format(len(elems)))

    exporter = Exporter(wallet_address)
    atom.processor.process_txs(wallet_address, elems, exporter)

    return exporter


def _query_blockchain(wallet_address, limit, page, chain_id, sender=True):
    """ Query terra blockchain for transactions as sender and receiver.  Get json response.  """

    if sender:
        events = "message.sender={}".format(wallet_address)
    else:
        events = "transfer.recipient={}".format(wallet_address)

    line = "gaiad query txs --events '{}' ".format(events)
    line += "--limit {} --node '{}' --page {} --chain-id '{}' --home {} ".format(limit, ATOM_NODE, page, chain_id, HOME)
    line += "| python3 -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin, Loader=yaml.FullLoader), sys.stdout, indent=4)'"

    # Run query
    json_string = _cmd(line)

    try:
        data = json.loads(json_string)
    except JSONDecodeError as e:
        time.sleep(5)
        logging.info("Failed query.  Retrying once... json_string=%s", json_string)
        # Retry once.
        json_string = _cmd(line)
        data = json.loads(json_string)

    time.sleep(5)
    return data


def _count_txs(wallet_address):
    pages = []
    for chain_id in CHAIN_IDS:

        sender = True
        data = _query_blockchain(wallet_address, 10, 1, chain_id, sender)
        page_nums = _pages(data)
        for page_num in page_nums:
            pages.append((chain_id, page_num, sender))

        sender = False
        data = _query_blockchain(wallet_address, 10, 1, chain_id, sender)
        page_nums = _pages(data)
        for page_num in page_nums:
            pages.append((chain_id, page_num, sender))

    return pages


def _pages(data):
    count = int(data["total_count"])
    page_total = int((count - 1) / LIMIT) + 1
    page_min = max(page_total - MAX_PAGES + 1, 1)
    pages = list(range(page_min, page_total + 1))
    return pages


def _fetch_txs(wallet_address, pages, progress):
    # Debugging only
    DEBUG_FILE = "_reports/testatom.{}.json".format(wallet_address)
    if localconfig.debug and os.path.exists(DEBUG_FILE):
        with open(DEBUG_FILE, 'r') as f:
            out = json.load(f)
            return out

    out = []
    for page in pages:
        chain_id, page_num, sender = page
        message = "Fetching page {} of {}...".format(page_num, len(pages))
        progress.report(page, message)
        data = _query_blockchain(wallet_address, limit=LIMIT, page=page_num, chain_id=chain_id, sender=sender)

        out.extend(data["txs"])

    out = _remove_duplicates(out)

    # Debugging only
    if localconfig.debug:
        with open(DEBUG_FILE, 'w') as f:
            json.dump(out, f, indent=4)
        logging.info("Wrote to %s for debugging", DEBUG_FILE)

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
