"""
usage: python3 report_fet.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/HUAHUA*.csv

TODO: fetchhub-2 transactions
  * requires significant work with querying/parsing legacy rpc api data.
"""

import logging
import pprint

from fet.config_fet import localconfig
from fet.progress_fet import SECONDS_PER_PAGE, ProgressFet
from common import report_util
from common.Cache import Cache
from common.Exporter import Exporter
from common.ExporterTypes import FORMAT_DEFAULT
from settings_csv import TICKER_FET, FET_NODE
import fet.processor
import common.ibc.api_lcd


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_FET)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_FET, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return common.ibc.api_lcd.LcdAPI(FET_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = common.ibc.api_lcd.LcdAPI(FET_NODE).get_tx(txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_FET)
    txinfo = fet.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * common.ibc.api_lcd.get_txs_pages_count(FET_NODE, wallet_address, max_txs)


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressFet()
    exporter = Exporter(wallet_address, localconfig, TICKER_FET)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = common.ibc.api_lcd.get_txs_pages_count(FET_NODE, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = common.ibc.api_lcd.get_txs_all(FET_NODE, wallet_address, progress, max_txs, debug=localconfig.debug)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    fet.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
