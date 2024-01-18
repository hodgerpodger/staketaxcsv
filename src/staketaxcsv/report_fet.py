"""
usage: python3 staketaxcsv/report_fet.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/FET*.csv
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.fet.fetchhub1.processor_legacy
import staketaxcsv.fet.processor
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ibc.constants import EVENTS_TYPE_SENDER, EVENTS_TYPE_RECIPIENT, EVENTS_TYPE_SIGNER
from staketaxcsv.fet.config_fet import localconfig
from staketaxcsv.fet.fetchhub1 import constants as co2
from staketaxcsv.fet.fetchhub1.api_rpc import FetRpcAPI
from staketaxcsv.fet.progress_fet import SECONDS_PER_PAGE, ProgressFet
from staketaxcsv.settings_csv import FET_NODE, TICKER_FET
from staketaxcsv.common.ibc.decorators import set_ibc_cache

EVENTS_TYPES_FET = (EVENTS_TYPE_SENDER, EVENTS_TYPE_RECIPIENT)


def main():
    report_util.main_default(TICKER_FET)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(FET_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    exporter = Exporter(wallet_address, localconfig, TICKER_FET)

    elem, node = _query_tx(txid)
    if not elem:
        print("txone(): Unable to find txid={}".format(txid))
        return exporter

    txinfo = staketaxcsv.fet.processor.process_tx(wallet_address, elem, exporter, node)

    return exporter


def _query_tx(txid):
    # fetchhub-4
    node = FET_NODE
    elem = staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1(node).get_tx(txid)
    if elem:
        return elem, node

    # fetchhub-3
    node = co2.FET_FETCHUB3_NODE
    elem = staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1(node).get_tx(txid)
    if elem:
        return elem, node

    # fetchhub-2
    node = co2.FET_FETCHUB2_NODE
    elem = staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1(node).get_tx(txid)
    if elem:
        return elem, node

    # fetchhub-1
    node = co2.FET_FETCHUB1_NODE
    elem = FetRpcAPI(node).tx(txid)
    if elem:
        return elem, node

    return None, None


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_lcd_v1.get_txs_pages_count(FET_NODE, wallet_address, max_txs)


@set_ibc_cache()
def txhistory(wallet_address):
    max_txs = localconfig.limit
    progress = ProgressFet()
    exporter = Exporter(wallet_address, localconfig, TICKER_FET)

    # Fetch count of pages/transactions to estimate progress more accurately
    pages_fet1, txs_fet1 = staketaxcsv.fet.fetchhub1.api_rpc.get_txs_pages_count(
        co2.FET_FETCHUB1_NODE, wallet_address, max_txs, events_types=EVENTS_TYPES_FET)
    pages_fet2 = staketaxcsv.common.ibc.api_lcd_v1.get_txs_pages_count(
        co2.FET_FETCHUB2_NODE, wallet_address, max_txs, events_types=EVENTS_TYPES_FET)
    pages_fet3 = staketaxcsv.common.ibc.api_lcd_v1.get_txs_pages_count(
        co2.FET_FETCHUB3_NODE, wallet_address, max_txs, events_types=EVENTS_TYPES_FET)
    pages_fet4 = staketaxcsv.common.ibc.api_lcd_v1.get_txs_pages_count(
        FET_NODE, wallet_address, max_txs, events_types=EVENTS_TYPES_FET)
    progress.set_estimate_fet1(pages_fet1, txs_fet1)
    progress.set_estimate_fet2(pages_fet2)
    progress.set_estimate_fet3(pages_fet3)
    progress.set_estimate_fet4(pages_fet4)

    # fetchhub1
    elems_1 = staketaxcsv.fet.fetchhub1.api_rpc.get_txs_all(
        co2.FET_FETCHUB1_NODE, wallet_address, max_txs, progress=progress,
        stage_name=progress.STAGE_FET1_PAGES, events_types=EVENTS_TYPES_FET)
    # Update to more accurate estimate after removing duplicates
    progress.stages[progress.STAGE_FET1_TXS].total_tasks = len(elems_1)
    progress.report_message(f"Processing {len(elems_1)} transactions for fetchhub-1... ")
    staketaxcsv.fet.processor.process_txs(wallet_address, elems_1, exporter, co2.FET_FETCHUB1_NODE, progress)

    # fetchhub2
    elems_2 = staketaxcsv.common.ibc.api_lcd_v1.get_txs_all(
        co2.FET_FETCHUB2_NODE, wallet_address, max_txs, progress=progress,
        stage_name=progress.STAGE_FET2, events_types=EVENTS_TYPES_FET)
    progress.report_message(f"Processing {len(elems_2)} transactions for fetchhub-2... ")
    staketaxcsv.fet.processor.process_txs(wallet_address, elems_2, exporter, co2.FET_FETCHUB2_NODE)

    # fetchhub3
    elems_3 = staketaxcsv.common.ibc.api_lcd_v1.get_txs_all(
        co2.FET_FETCHUB3_NODE, wallet_address, max_txs, progress=progress,
        stage_name=progress.STAGE_FET3, events_types=EVENTS_TYPES_FET)
    progress.report_message(f"Processing {len(elems_3)} transactions for fetchhub-3... ")
    staketaxcsv.fet.processor.process_txs(wallet_address, elems_3, exporter, co2.FET_FETCHUB3_NODE)

    # fetchhub4
    elems_4 = staketaxcsv.common.ibc.api_lcd_v1.get_txs_all(
        FET_NODE, wallet_address, max_txs, progress=progress,
        stage_name=progress.STAGE_FET4, events_types=EVENTS_TYPES_FET
    )
    progress.report_message(f"Processing {len(elems_4)} transactions for fetchhub-4... ")
    staketaxcsv.fet.processor.process_txs(wallet_address, elems_4, exporter, FET_NODE)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
