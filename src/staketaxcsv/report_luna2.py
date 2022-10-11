"""
usage: python3 report_luna2.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/LUNA2*.csv

Notes:
    * Terra 2.0 (aka "LUNA 2.0")
    * https://fcd.terra.dev/swagger
    * https://phoenix-lcd.terra.dev/swagger/

"""

import logging
import math
import pprint

import staketaxcsv.common.ibc.api_common
import staketaxcsv.common.ibc.api_lcd
import staketaxcsv.luna2.genesis_airdrop
import staketaxcsv.luna2.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import FORMAT_DEFAULT
from staketaxcsv.luna2.api_fcd import LIMIT_FCD, FcdAPI
from staketaxcsv.luna2.config_luna2 import localconfig
from staketaxcsv.luna2.progress_luna2 import SECONDS_PER_PAGE, ProgressLuna2
from staketaxcsv.settings_csv import LUNA2_LCD_NODE, TICKER_LUNA2


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_LUNA2)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_LUNA2, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd.LcdAPI(LUNA2_LCD_NODE).account_exists(wallet_address)


def estimate_duration(wallet_address, options):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(LUNA2_LCD_NODE, wallet_address, max_txs)


def txone(wallet_address, txid):
    data = FcdAPI.get_tx(txid)
    print("\ndebug data:")
    pprint.pprint(data)
    print("")

    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA2)
    txinfo = staketaxcsv.luna2.processor.process_tx(wallet_address, data, exporter)
    txinfo.print()
    print("")

    return exporter


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        cache = Cache()
        _cache_load(cache)

    max_txs = localconfig.limit
    progress = ProgressLuna2()
    exporter = Exporter(wallet_address, localconfig, TICKER_LUNA2)

    # Fetch/add genesis airdrop to csv
    progress.report_message("Fetching genesis airdrop amount...")
    staketaxcsv.luna2.genesis_airdrop.genesis_airdrop(wallet_address, exporter)

    # LCD - fetch count of transactions to estimate progress more accurately
    pages = staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(LUNA2_LCD_NODE, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_estimate(pages)

    # FCD - fetch transactions
    elems = _get_txs(wallet_address, progress)

    # Process all transactions
    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.luna2.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        _cache_push(cache)

    return exporter


def _cache_load(cache):
    localconfig.ibc_addresses = cache.get_ibc_addresses()
    localconfig.contracts = cache.get_luna2_contracts()
    localconfig.currency_addresses = cache.get_luna2_currency_addresses()
    localconfig.lp_currency_addresses = cache.get_luna2_lp_currency_addresses()
    logging.info("_cache_load(): downloaded data from cache ...")


def _cache_push(cache):
    cache.set_ibc_addresses(localconfig.ibc_addresses)
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
