"""
usage: python3 staketaxcsv/report_luna2.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/LUNA2*.csv

Notes:
    * Terra 2.0 (aka "LUNA 2.0")
    * https://fcd.terra.dev/swagger
    * https://phoenix-lcd.terra.dev/swagger/

"""

import logging
import math
import pprint

import staketaxcsv.api
import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.luna2.genesis_airdrops
import staketaxcsv.luna2.processor
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.luna2.api_fcd import LIMIT_FCD, FcdAPI
from staketaxcsv.luna2.config_luna2 import localconfig
from staketaxcsv.luna2.progress_luna2 import SECONDS_PER_PAGE, ProgressLuna2
from staketaxcsv.settings_csv import LUNA2_NODE, TICKER_LUNA2
from staketaxcsv.common.ibc.decorators import set_ibc_cache
from staketaxcsv import settings_csv


def main():
    report_util.main_default(TICKER_LUNA2)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    localconfig.include_tiny_vesting = options.get("include_tiny_vesting", localconfig.include_tiny_vesting)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(LUNA2_NODE).account_exists(wallet_address)


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * api_lcd.get_txs_pages_count(LUNA2_NODE, wallet_address, max_txs)


def txone(wallet_address, txid):
    data = FcdAPI.get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA2)
    txinfo = staketaxcsv.luna2.processor.process_tx(wallet_address, data, exporter)

    if localconfig.debug:
        logging.info("txinfo:")
        txinfo.print()

    return exporter


@set_ibc_cache()
def txhistory(wallet_address):
    if settings_csv.DB_CACHE:
        cache = Cache()
        _cache_load(cache)

    max_txs = localconfig.limit
    progress = ProgressLuna2()
    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA2)

    # Fetch/add genesis airdrop to csv
    progress.report_message("Fetching genesis airdrop amount...")
    staketaxcsv.luna2.genesis_airdrops.genesis_airdrops(wallet_address, exporter)

    # LCD - fetch count of transactions to estimate progress more accurately
    pages = api_lcd.get_txs_pages_count(LUNA2_NODE, wallet_address, max_txs)
    progress.set_estimate(pages)

    # FCD - fetch transactions
    elems = _get_txs(wallet_address, progress)

    # Process all transactions
    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.luna2.processor.process_txs(wallet_address, elems, exporter)

    if settings_csv.DB_CACHE:
        _cache_push(cache)

    return exporter


def _cache_load(cache):
    localconfig.contracts = cache.get_luna2_contracts()
    localconfig.currency_addresses = cache.get_luna2_currency_addresses()
    localconfig.lp_currency_addresses = cache.get_luna2_lp_currency_addresses()
    logging.info("_cache_load(): downloaded data from cache ...")


def _cache_push(cache):
    cache.set_luna2_contracts(localconfig.contracts)
    cache.set_luna2_currency_addresses(localconfig.currency_addresses)
    cache.set_luna2_lp_currency_addresses(localconfig.lp_currency_addresses)
    logging.info("_cache_push(): push data to cache")


def _max_queries():
    max_txs = localconfig.limit
    max_queries = math.ceil(max_txs / LIMIT_FCD)
    logging.info("max_txs: %s, max_queries: %s", max_txs, max_queries)
    return max_queries


def _get_txs(wallet_address, progress):
    offset = 0
    out = []
    for _ in range(_max_queries()):
        num_tx = len(out)
        progress.report(num_tx, f"Retrieving transaction {num_tx + 1} ...")

        data = FcdAPI.get_txs(wallet_address, offset)
        result = data["txs"]
        out.extend(result)

        if data.get("next", None):
            offset = data["next"]
        else:
            break

    message = f"Retrieved total {len(out)} txids..."
    progress.report_message(message)

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
