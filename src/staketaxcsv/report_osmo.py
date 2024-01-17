"""
usage: python3 staketaxcsv/report_osmo.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/OSMO*.csv

"""
import logging
import math
import pprint

import staketaxcsv.osmo.api_data
import staketaxcsv.osmo.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import LP_TREATMENT_TRANSFERS
from staketaxcsv.common.ExporterBalances import ExporterBalance
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo.lp_rewards import lp_rewards
from staketaxcsv.osmo.progress_osmo import ProgressOsmo
from staketaxcsv.settings_csv import TICKER_OSMO
from staketaxcsv.common.ibc.tx_data import TxDataMintscan
from staketaxcsv.common.ibc.progress_mintscan import SECONDS_PER_PAGE
from staketaxcsv.common.ibc import historical_balances


def main():
    report_util.main_default(TICKER_OSMO)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)

    localconfig.lp_treatment = options.get("lp_treatment", LP_TREATMENT_TRANSFERS)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataMintscan(TICKER_OSMO, max_txs)


def wallet_exists(wallet_address):
    if not wallet_address.startswith("osmo"):
        return False
    count = staketaxcsv.osmo.api_data.get_count_txs(wallet_address)
    return count > 0


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_OSMO)
    txinfo = staketaxcsv.osmo.processor.process_tx(wallet_address, elem, exporter)

    if localconfig.debug:
        print("txinfo:")
        txinfo.print()

    return exporter


def estimate_duration(wallet_address):
    start_date, end_date = localconfig.start_date, localconfig.end_date
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address, start_date, end_date)


def txhistory(wallet_address):
    if localconfig.cache:
        cache = Cache()
        _cache_load(cache)

    start_date, end_date = localconfig.start_date, localconfig.end_date
    progress = ProgressOsmo(localconfig)
    exporter = Exporter(wallet_address, localconfig, TICKER_OSMO)
    txdata = _txdata()

    # Set time estimate to estimate progress later
    count_pages = txdata.get_txs_pages_count(wallet_address, start_date, end_date)
    progress.set_estimate(count_pages)
    reward_tokens = staketaxcsv.osmo.api_data.get_lp_tokens(wallet_address)
    progress.set_estimate_lp_rewards_stage(len(reward_tokens))
    logging.info("pages: %s, reward_tokens: %s", count_pages, reward_tokens)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress, start_date, end_date)

    # Process transactions
    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.osmo.processor.process_txs(wallet_address, elems, exporter)

    # Fetch & process LP rewards data
    lp_rewards(wallet_address, reward_tokens, exporter, progress)

    exporter.sort_rows(reverse=True)

    # Log error stats if exists
    ErrorCounter.log(TICKER_OSMO, wallet_address)

    if localconfig.cache:
        _cache_push(cache)
    return exporter


def _cache_load(cache):
    localconfig.ibc_addresses = cache.get_ibc_addresses()
    localconfig.exponents = cache.get_osmo_exponents()

    logging.info("_cache_load(): downloaded data from cache ...")


def _cache_push(cache):
    cache.set_ibc_addresses(localconfig.ibc_addresses)
    cache.set_osmo_exponents(localconfig.exponents)

    logging.info("_cache_push(): push data to cache")


def balances(wallet_address):
    start_date, end_date = localconfig.start_date, localconfig.end_date
    max_txs = localconfig.limit

    exporter = historical_balances.via_mintscan("uosmo", TICKER_OSMO, wallet_address, max_txs, start_date, end_date)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
