"""
usage: python3 report_kuji.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/KUJI*.csv
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd
import staketaxcsv.kuji.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import FORMAT_DEFAULT
from staketaxcsv.kuji.config_kuji import localconfig
from staketaxcsv.kuji.progress_kuji import SECONDS_PER_PAGE, ProgressKuji
from staketaxcsv.settings_csv import KUJI_NODE, TICKER_KUJI


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_KUJI)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_KUJI, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd.LcdAPI(KUJI_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_lcd.LcdAPI(KUJI_NODE).get_tx(txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_KUJI)
    txinfo = staketaxcsv.kuji.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address, options):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(KUJI_NODE, wallet_address, max_txs)


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressKuji()
    exporter = Exporter(wallet_address, localconfig, TICKER_KUJI)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(KUJI_NODE, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = staketaxcsv.common.ibc.api_lcd.get_txs_all(KUJI_NODE, wallet_address, progress, max_txs, debug=localconfig.debug)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.kuji.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
