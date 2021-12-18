
"""
usage: python3 report_sol.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/SOL*.csv
"""

import logging
import json
from json.decoder import JSONDecodeError
import os

from common.Cache import Cache
from common.Exporter import Exporter
from common import report_util
from settings_csv import TICKER_SOL, MESSAGE_STAKING_ADDRESS_FOUND, MESSAGE_ADDRESS_NOT_FOUND, SOL_NODE
import sol.processor
from sol.ProgressSol import ProgressSol, SECONDS_PER_STAKING_ADDRESS, SECONDS_PER_TX
from sol.config_sol import localconfig
from sol.constants import PROGRAMID_STAKE
from sol.api_rpc import RpcAPI
from sol import staking_rewards
from common.ErrorCounter import ErrorCounter

LIMIT = 1000
MAX_TRANSACTIONS = 5000
# MAX_QUERIES = int(MAX_TRANSACTIONS / LIMIT)
RPC_TIMEOUT = 600  # seconds


def main():
    wallet_address, format, txid, options = report_util.parse_args()
    readOptions(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address)
        report_util.run_exports(TICKER_SOL, wallet_address, exporter, format)


def readOptions(options):
    if options:
        if options.get("debug") is True:
            localconfig.debug = True
        if options.get("cache") is True:
            localconfig.cache = True
        if options.get("limit"):
            localconfig.limit = options.get("limit")


def wallet_exists(wallet_address):
    is_wallet_address, is_staking_address = _account_exists(wallet_address)
    if is_wallet_address:
        return True, None
    if is_staking_address:
        return False, MESSAGE_STAKING_ADDRESS_FOUND
    if _has_transaction(wallet_address):
        return True, None

    return False, MESSAGE_ADDRESS_NOT_FOUND


def _has_transaction(wallet_address):
    txids, _ = RpcAPI.get_txids(wallet_address, limit=2)
    return len(txids) > 0


def _account_exists(wallet_address):
    data = RpcAPI.fetch_account(wallet_address)

    if "result" not in data:
        return False, False
    if "error" in data:
        return False, False

    try:
        owner = data["result"]["value"]["owner"]
        if owner == PROGRAMID_STAKE:
            return False, True
        else:
            return True, False
    except (JSONDecodeError, TypeError):
        return False, False


def txone(wallet_address, txid):
    data = RpcAPI.fetch_tx(txid)
    s = json.dumps(data, indent=4)
    print("\nTransaction data:")
    print(s)
    print("\n")

    exporter = Exporter(wallet_address)
    txinfo = sol.processor.process_tx(wallet_address, exporter, txid, data)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address):
    logging.info("Fetching staking addresses...")
    num_staking_addresses = len(RpcAPI.fetch_staking_addresses(wallet_address))
    logging.info("Fetching txids...")
    num_txids = _num_txids(wallet_address)
    return SECONDS_PER_STAKING_ADDRESS * num_staking_addresses + SECONDS_PER_TX * num_txids


def _num_txids(wallet_address):
    txids = _query_txids([wallet_address], None)
    return len(txids)


def txhistory(wallet_address, job=None):
    progress = ProgressSol()

    logging.info("Using SOLANA_URL=%s...", SOL_NODE)
    if job:
        localconfig.job = job
        localconfig.cache = True
    if localconfig.cache:
        localconfig.blocks = Cache().get_sol_blocks()
        logging.info("Loaded sol blocks info into cache...")

    # Fetch staking addresses of this wallet
    progress.report_message("Fetching staking addresses...")
    staking_addresses = RpcAPI.fetch_staking_addresses(wallet_address)
    logging.info("staking_addresses: %s", staking_addresses)

    # Fetch transaction ids for wallet
    txids = _txids(wallet_address, progress)

    # Update parameters to calculate progress more accurately later
    progress.set_estimate(len(staking_addresses), len(txids))

    # Fetch staking rewards data
    exporter = Exporter(wallet_address)
    staking_rewards.reward_txs(staking_addresses, wallet_address, exporter, progress)

    # Fetch transaction data and create rows for CSV
    _process_txs(txids, wallet_address, exporter, progress)

    ErrorCounter.log(TICKER_SOL, wallet_address)

    if localconfig.cache:
        # Flush cache to db
        Cache().set_sol_blocks(localconfig.blocks)

    return exporter


def _max_queries():
    max_txs = localconfig.limit if localconfig.limit else MAX_TRANSACTIONS
    max_queries = int(max_txs / LIMIT) + 1
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def _query_txids(addresses, progress):
    """ Returns transactions txid's across all token account addresses """
    max_queries = _max_queries()

    out = []
    before = None
    for i, address in enumerate(addresses):
        if progress and i % 10 == 0:
            message = "Fetched txids for {} of {} addresses...".format(i, len(addresses))
            progress.report_message(message)

        # Get transaction txids for this token account
        for j in range(max_queries):
            logging.info("query %s for address=%s", j, address)

            txids, before = RpcAPI.get_txids(address, limit=LIMIT, before=before)
            out.extend(txids)

            if before is None:
                break

    # Remove duplicates
    out2 = []
    txids_seen = set()
    for txid in out:
        if txid in txids_seen:
            continue
        txids_seen.add(txid)

        out2.append(txid)

    # Process oldest first
    out2.reverse()
    return out2


def _txids(wallet_address, progress):
    # Debugging only
    DEBUG_FILE = "_reports/debugsol.{}.transactions.json".format(wallet_address)
    if localconfig.debug and os.path.exists(DEBUG_FILE):
        logging.info("Debug mode: reading from %s", DEBUG_FILE)
        with open(DEBUG_FILE, 'r') as f:
            out = json.load(f)
            return out

    # Sometimes, transactions do not all appear under main wallet address when querying transaction history.
    # So retrieve token addresses too.
    addresses = [wallet_address]
    token_accounts = RpcAPI.fetch_token_accounts(wallet_address).keys()
    addresses.extend(token_accounts)

    out = _query_txids(addresses, progress)

    # Debugging only
    if localconfig.debug:
        with open(DEBUG_FILE, 'w') as f:
            json.dump(out, f, indent=4)
            logging.info("Wrote to %s for debugging", DEBUG_FILE)

    logging.info("Finished retrieving all txids.  length=%s", len(out))
    return out


def _process_txs(txids, wallet_address, exporter, progress):
    for i, txid in enumerate(txids):
        data = RpcAPI.fetch_tx(txid)
        sol.processor.process_tx(wallet_address, exporter, txid, data)

        if i % 10 == 0:
            # Update progress to db every so often for user
            message = "Processed {} of {} transactions".format(i + 1, len(txids))
            progress.report("_process_txs", i, message)

    progress.report("_process_txs", len(txids), "Finished processing {} transactions".format(len(txids)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
