"""
usage: python3 staketaxcsv/report_sol.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/SOL*.csv
"""

import logging
from json.decoder import JSONDecodeError
import pprint


import staketaxcsv.sol.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import MESSAGE_ADDRESS_NOT_FOUND, MESSAGE_STAKING_ADDRESS_FOUND, SOL_NODE, TICKER_SOL
from staketaxcsv.sol import staking_rewards
from staketaxcsv.sol.api_rpc import RpcAPI
from staketaxcsv.sol.config_sol import localconfig
from staketaxcsv.sol.constants import PROGRAMID_STAKE
from staketaxcsv.sol.progress_sol import SECONDS_PER_STAKING_ADDRESS, SECONDS_PER_TX, ProgressSol
from staketaxcsv.sol.TxInfoSol import WalletInfo
from staketaxcsv.sol.txids import get_txids, get_txids_for_accounts


RPC_TIMEOUT = 600  # seconds


def main():
    report_util.main_default(TICKER_SOL)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    localconfig.start_date = options.get("start_date", None)
    localconfig.end_date = options.get("end_date", None)
    localconfig.exclude_failed = options.get("exclude_failed", localconfig.exclude_failed)
    localconfig.exclude_associated = options.get("exclude_associated", localconfig.exclude_associated)
    logging.info("localconfig: %s", localconfig.__dict__)


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

    if localconfig.debug:
        print("tx data:")
        pprint.pprint(data)

    exporter = Exporter(wallet_address, localconfig, TICKER_SOL)
    txinfo = staketaxcsv.sol.processor.process_tx(WalletInfo(wallet_address), exporter, txid, data)

    if localconfig.debug:
        print("txinfo:")
        txinfo.print()

    return exporter


def estimate_duration(wallet_address):
    start_date, end_date = localconfig.start_date, localconfig.end_date

    logging.info("Fetching staking addresses...")
    num_staking_addresses = len(RpcAPI.fetch_staking_addresses(wallet_address))

    logging.info("Fetching txids...")
    num_txids = len(
        get_txids_for_accounts([wallet_address], progress=None, start_date=start_date, end_date=end_date)
    )

    return SECONDS_PER_STAKING_ADDRESS * num_staking_addresses + SECONDS_PER_TX * num_txids


def txhistory(wallet_address):
    logging.info("Using SOLANA_URL=%s...", SOL_NODE)
    start_date, end_date = localconfig.start_date, localconfig.end_date

    progress = ProgressSol()
    exporter = Exporter(wallet_address, localconfig, TICKER_SOL)
    wallet_info = WalletInfo(wallet_address)

    # ####### Fetch data to so that job progress can be estimated ##########

    # Fetch transaction ids for wallet
    txids = get_txids(wallet_address, progress, start_date, end_date)

    # Fetch current staking addresses for wallet
    progress.report_message("Fetching staking addresses...")
    for addr in RpcAPI.fetch_staking_addresses(wallet_address):
        wallet_info.add_staking_address(addr)

    # Update progress indicator
    progress.set_estimate(len(wallet_info.get_staking_addresses()), len(txids))

    ########################################################################

    # Transactions data
    _fetch_and_process_txs(txids, wallet_info, exporter, progress)

    # Update progress indicator
    progress.update_estimate(len(wallet_info.get_staking_addresses()))

    # Staking rewards data
    staking_rewards.reward_txs(wallet_info, exporter, progress, start_date, end_date)

    ErrorCounter.log(TICKER_SOL, wallet_address)
    return exporter


def _fetch_and_process_txs(txids, wallet_info, exporter, progress=None):
    total_count = len(txids)

    for i, txid in enumerate(txids):
        elem = RpcAPI.fetch_tx(txid)
        staketaxcsv.sol.processor.process_tx(wallet_info, exporter, txid, elem)

        if progress and i % 10 == 0:
            # Update progress to db every so often for user
            message = f"Fetched {i + 1} of {total_count} transactions"
            progress.report(i, message, "txs")

    if progress:
        message = f"Finished fetching {total_count} transactions"
        progress.report(total_count, message, "txs")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
