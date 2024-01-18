"""
usage: python3 staketaxcsv/report_btsg.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/BTSG*.csv
"""

import logging

import staketaxcsv.btsg.processor
from staketaxcsv.btsg.config_btsg import localconfig
from staketaxcsv.btsg.progress_btsg import SECONDS_PER_PAGE, ProgressBTSG
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import BTSG_NODE, TICKER_BTSG
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.tx_data import TxDataLcd
from staketaxcsv.common.ibc.decorators import set_ibc_cache


def main():
    report_util.main_default(TICKER_BTSG)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataLcd(BTSG_NODE, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(BTSG_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_BTSG)
    txinfo = staketaxcsv.btsg.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


@set_ibc_cache()
def txhistory(wallet_address):
    progress = ProgressBTSG()
    exporter = Exporter(wallet_address, localconfig, TICKER_BTSG)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.btsg.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
