"""
usage: python3 staketaxcsv/report_huahua.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/HUAHUA*.csv
"""

import logging
import pprint

import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.huahua.processor
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.huahua.config_huahua import localconfig
from staketaxcsv.huahua.progress_huahua import SECONDS_PER_PAGE, ProgressHuahua
from staketaxcsv.settings_csv import HUAHUA_NODE, TICKER_HUAHUA
from staketaxcsv.common.ibc.tx_data import TxDataLcd
from staketaxcsv.common.ibc.decorators import set_ibc_cache
LIMIT_PER_QUERY = 10


def main():
    report_util.main_default(TICKER_HUAHUA)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataLcd(HUAHUA_NODE, max_txs, limit_per_query=LIMIT_PER_QUERY)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(HUAHUA_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_HUAHUA)
    txinfo = staketaxcsv.huahua.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


@set_ibc_cache()
def txhistory(wallet_address):
    progress = ProgressHuahua()
    exporter = Exporter(wallet_address, localconfig, TICKER_HUAHUA)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.huahua.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
