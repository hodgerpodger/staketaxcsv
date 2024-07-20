"""
usage: python3 staketaxcsv/report_stars.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/STARS*.csv

TODO: STARS CSVs are only in experimental state.  All "execute contract" transactions are still treated as
      unknown transactions.
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_rpc_multinode
import staketaxcsv.stars.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import STARS_NODE, TICKER_STARS, STARS_NODE_RPC
from staketaxcsv.stars.config_stars import localconfig
from staketaxcsv.stars.progress_stars import SECONDS_PER_PAGE, ProgressStars, SECONDS_PER_TX
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.tx_data import TxDataLcd, TxDataRpc
from staketaxcsv.common.ibc.decorators import set_ibc_cache
STARS_NODES_RPC = [STARS_NODE_RPC]


def main():
    report_util.main_default(TICKER_STARS)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataRpc(STARS_NODES_RPC, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(STARS_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_STARS)
    txinfo = staketaxcsv.stars.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    num_pages, num_txs = _txdata().get_txs_pages_count(wallet_address)
    return SECONDS_PER_PAGE * num_pages + SECONDS_PER_TX * num_txs


@set_ibc_cache()
def txhistory(wallet_address):
    progress = ProgressStars()
    exporter = Exporter(wallet_address, localconfig, TICKER_STARS)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress beforehand
    txdata.get_txs_pages_count(wallet_address, progress_rpc=progress)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.stars.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
