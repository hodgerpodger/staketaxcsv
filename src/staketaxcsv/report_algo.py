"""
usage: python3 staketaxcsv/report_algo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/ALGO.<walletaddress>.<format>.csv
"""

import json
import logging
import os

import staketaxcsv.algo.processor
from staketaxcsv.algo.api.indexer import Indexer
from staketaxcsv.algo.api.nfdomains import NFDomains
from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.progress_algo import ProgressAlgo
from staketaxcsv.common import report_util
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import LP_TREATMENT_TRANSFERS
from staketaxcsv.settings_csv import REPORTS_DIR, TICKER_ALGO

indexer = Indexer()


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_ALGO)

    if wallet_address.endswith(".algo"):
        wallet_address = NFDomains().get_address(wallet_address)

    report_util.run_report(TICKER_ALGO, wallet_address, export_format, txid, options)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)

    localconfig.start_date = options.get("start_date", None)
    localconfig.end_date = options.get("end_date", None)
    localconfig.lp_treatment = options.get("lp_treatment", LP_TREATMENT_TRANSFERS)
    if "exclude_asas" in options:
        localconfig.exclude_asas = [asa.strip().lower() for asa in options["exclude_asas"].split(",")]
    localconfig.track_block = options.get("track_block", False)

    logging.info("localconfig: %s", localconfig.__dict__)


def _read_persistent_config(wallet_address):
    config_file = f"{REPORTS_DIR}/config.{TICKER_ALGO}.{wallet_address}.json"
    if localconfig.track_block and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            localconfig.min_round = config.get("min_round")
            logging.info(f"Starting from block {localconfig.min_round}")


def _write_persistent_config(wallet_address):
    if localconfig.track_block:
        config_file = f"{REPORTS_DIR}/config.{TICKER_ALGO}.{wallet_address}.json"
        with open(config_file, 'w') as f:
            config = {
                "min_round": localconfig.min_round
            }
            json.dump(config, f, indent=4)


def wallet_exists(wallet_address):
    return indexer.account_exists(wallet_address)


def txone(wallet_address, txid_or_groupid):
    indexer = Indexer()  # just to get unit test patch to work

    progress = ProgressAlgo()
    exporter = Exporter(wallet_address, localconfig, TICKER_ALGO)

    account = indexer.get_account(wallet_address)
    dapps = []
    for p in Dapp.plugins:
        plugin = p(indexer, wallet_address, account, exporter)
        logging.info("Loaded plugin for %s", plugin.name)
        dapps.append(plugin)

    elems = None
    data = indexer.get_transaction(txid_or_groupid)
    if data:
        if "group" in data:
            txid_or_groupid = data["group"]
        else:
            elems = [data]

    if elems is None:
        elems = indexer.get_transactions_by_group(txid_or_groupid)

    progress.set_estimate(1)
    staketaxcsv.algo.processor.process_txs(wallet_address, dapps, elems, exporter, progress)

    return exporter


def txhistory(wallet_address):
    _read_persistent_config(wallet_address)

    progress = ProgressAlgo()
    exporter = Exporter(wallet_address, localconfig, TICKER_ALGO)

    account = indexer.get_account(wallet_address)

    if account is not None:
        dapps = []
        for p in Dapp.plugins:
            plugin = p(indexer, wallet_address, account, exporter)
            logging.info("Loaded plugin for %s", plugin.name)
            dapps.append(plugin)

        # Retrieve data
        elems = _get_txs(wallet_address, dapps, progress)

        # Create rows for CSV
        staketaxcsv.algo.processor.process_txs(wallet_address, dapps, elems, exporter, progress)

        _write_persistent_config(wallet_address)
    else:
        logging.error("Failed to retrieve account %s", wallet_address)
        ErrorCounter.increment("indexer", wallet_address)

    # Log error stats if exists
    ErrorCounter.log(TICKER_ALGO, wallet_address)

    return exporter


def _get_txs(wallet_address, dapps, progress):
    out = indexer.get_all_transactions(wallet_address)

    if out:
        # Reverse the list so transactions are in chronological order
        out.reverse()
        last_round = 0
        if localconfig.track_block and len(out) > 0:
            last_round = out[-1]["confirmed-round"]

        for app in dapps:
            out.extend(app.get_extra_transactions())

        if last_round:
            localconfig.min_round = last_round + 1

    num_tx = len(out)
    progress.set_estimate(num_tx)
    message = "Retrieved total {} txids...".format(num_tx)
    progress.report_message(message)

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
