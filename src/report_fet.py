"""
usage: python3 report_fet.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/FET*.csv
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
import common.ibc.api_lcd
from fet.fetchhub1.api_rpc import RpcAPI
from fet.fetchhub1 import constants as co2
import fet.processor
import fet.fetchhub1.processor_legacy


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
    exporter = Exporter(wallet_address, localconfig, TICKER_FET)

    elem, node = _query_tx(txid)
    if not elem:
        print("txone(): Unable to find txid={}".format(txid))
        return exporter

    txinfo = fet.processor.process_tx(wallet_address, elem, exporter, node)

    print("Transaction data:")
    pprint.pprint(elem)
    txinfo.print()

    return exporter


def _query_tx(txid):
    # fetchhub-3
    node = FET_NODE
    elem = common.ibc.api_lcd.LcdAPI(node).get_tx(txid)
    if elem:
        return elem, node

    # fetchhub-2
    node = co2.FET_FETCHUB2_NODE
    elem = common.ibc.api_lcd.LcdAPI(node).get_tx(txid)
    if elem:
        return elem, node

    # fetchhub-1
    node = co2.FET_FETCHUB1_NODE
    elem = RpcAPI(node).tx(txid)
    if elem:
        return elem, node

    return None, None


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

    # Fetch count of pages/transactions to estimate progress more accurately
    pages_fet1, txs_fet1 = fet.fetchhub1.api_rpc.get_txs_pages_count(
        co2.FET_FETCHUB1_NODE, wallet_address, max_txs, debug=localconfig.debug)
    pages_fet2 = common.ibc.api_lcd.get_txs_pages_count(
        co2.FET_FETCHUB2_NODE, wallet_address, max_txs, debug=localconfig.debug)
    pages_fet3 = common.ibc.api_lcd.get_txs_pages_count(
        FET_NODE, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_estimate_fet1(pages_fet1, txs_fet1)
    progress.set_estimate_fet2(pages_fet2)
    progress.set_estimate_fet3(pages_fet3)

    # fetchhub1
    elems_1 = fet.fetchhub1.api_rpc.get_txs_all(
        co2.FET_FETCHUB1_NODE, wallet_address, progress, max_txs, debug=localconfig.debug,
        stage_name=progress.STAGE_FET1_PAGES)
    # Update to more accurate estimate after removing duplicates
    progress.stages[progress.STAGE_FET1_TXS].total_tasks = len(elems_1)
    progress.report_message(f"Processing {len(elems_1)} transactions for fetchhub-1... ")
    fet.processor.process_txs(wallet_address, elems_1, exporter, co2.FET_FETCHUB1_NODE, progress)

    # fetchhub2
    elems_2 = common.ibc.api_lcd.get_txs_all(
        co2.FET_FETCHUB2_NODE, wallet_address, progress, max_txs, debug=localconfig.debug,
        stage_name=progress.STAGE_FET2)
    progress.report_message(f"Processing {len(elems_2)} transactions for fetchhub-2... ")
    fet.processor.process_txs(wallet_address, elems_2, exporter, co2.FET_FETCHUB2_NODE)

    # fetchhub3
    elems_3 = common.ibc.api_lcd.get_txs_all(
        FET_NODE, wallet_address, progress, max_txs, debug=localconfig.debug, stage_name=progress.STAGE_FET3)
    progress.report_message(f"Processing {len(elems_3)} transactions for fetchhub-3... ")
    fet.processor.process_txs(wallet_address, elems_3, exporter, FET_NODE)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
