
"""
usage: python3 report_sol.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/SOL*.csv
"""

import logging
import json
from json.decoder import JSONDecodeError
import os
import math

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
from sol.TxInfoSol import WalletInfo

LIMIT = 1000
MAX_TRANSACTIONS = 5000
RPC_TIMEOUT = 600  # seconds


def main():
    wallet_address, format, txid, options = report_util.parse_args()
    _read_options(options)

    if txid:
        exporter = txone(wallet_address, txid)
        exporter.export_print()
    else:
        exporter = txhistory(wallet_address)
        report_util.run_exports(TICKER_SOL, wallet_address, exporter, format)


def _read_options(options):
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
    txinfo = sol.processor.process_tx(WalletInfo(wallet_address), exporter, txid, data)
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
    wallet_info = WalletInfo(wallet_address)
    exporter = Exporter(wallet_address)

    logging.info("Using SOLANA_URL=%s...", SOL_NODE)
    if job:
        localconfig.job = job
        localconfig.cache = True
    if localconfig.cache:
        localconfig.blocks = Cache().get_sol_blocks()
        logging.info("Loaded sol blocks info into cache...")

    # Fetch data to so that job progress can be estimated ##########

    # Fetch transaction ids for wallet
    txids = _txids(wallet_address, progress)

    # Fetch current staking addresses for wallet
    progress.report_message("Fetching staking addresses...")
    for addr in RpcAPI.fetch_staking_addresses(wallet_address):
        wallet_info.add_staking_address(addr)

    # Update progress indicator
    progress.set_estimate(len(wallet_info.get_staking_addresses()), len(txids))

    #################################################################

    # Transactions data
    _fetch_and_process_txs(txids, wallet_info, exporter, progress)

    # Update progress indicator
    progress.num_staking_addresses = len(wallet_info.get_staking_addresses())

    # Staking rewards data
    staking_rewards.reward_txs(wallet_info, exporter, progress)

    ErrorCounter.log(TICKER_SOL, wallet_address)
    if localconfig.cache:
        # Flush cache to db
        Cache().set_sol_blocks(localconfig.blocks)

    return exporter


def _max_queries():
    """ Calculated max number of queries based off of config limits """
    max_txs = localconfig.limit if localconfig.limit else MAX_TRANSACTIONS
    max_queries = math.ceil(max_txs / LIMIT)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def _query_txids(addresses, progress):
    """ Returns transactions txid's across all token account addresses """
    max_queries = _max_queries()

    out = []
    txids_seen = set()
    for i, address in enumerate(addresses):
        if progress and i % 10 == 0:
            message = "Fetched txids for {} of {} addresses...".format(i, len(addresses))
            progress.report_message(message)

        # Get transaction txids for this token account
        before = None
        for j in range(max_queries):
            logging.info("query %s for address=%s", j, address)

            txids, before = RpcAPI.get_txids(address, limit=LIMIT, before=before)
            for txid in txids:
                # Remove duplicate txids
                if txid not in txids_seen:
                    out.append(txid)
                    txids_seen.add(txid)

            if before is None:
                break

    # Process oldest first
    out.reverse()
    return out


def _txids(wallet_address, progress):
    # Sometimes, transactions do not all appear under main wallet address when querying transaction history.
    # So retrieve token addresses too.
    addresses = [wallet_address]
    token_accounts = RpcAPI.fetch_token_accounts(wallet_address).keys()
    addresses.extend(token_accounts)

    out = _query_txids(addresses, progress)
    return out


def _fetch_and_process_txs(txids, wallet_info, exporter, progress):
    total_count = len(txids)

    for i, txid in enumerate(txids):
        elem = RpcAPI.fetch_tx(txid)
        sol.processor.process_tx(wallet_info, exporter, txid, elem)

        if i % 10 == 0:
            # Update progress to db every so often for user
            message = "Fetched {} of {} transactions".format(i + 1, total_count)
            progress.report("txs", i, message)

    message = "Finished fetching {} transactions".format(total_count)
    progress.report("txs", total_count, message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
