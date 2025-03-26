"""
usage: python3 staketaxcsv/report_saga.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/SAGA*.csv
"""

import logging


import staketaxcsv.saga.processor
from staketaxcsv.saga.config_saga import localconfig
from staketaxcsv.saga.progress import SECONDS_PER_PAGE, ProgressSaga
from staketaxcsv.saga.genesis import genesis_airdrop
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import SAGA_NODE, TICKER_SAGA
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.tx_data import TxDataLcd, TxDataMintscan
from staketaxcsv.common.ibc.decorators import set_ibc_cache


def main():
    report_util.main_default(TICKER_SAGA)


def read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataMintscan(TICKER_SAGA, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(SAGA_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_SAGA)
    txinfo = staketaxcsv.saga.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


@set_ibc_cache()
def txhistory(wallet_address):
    """ Configure localconfig based on options dictionary. """
    progress = ProgressSaga()
    exporter = Exporter(wallet_address, localconfig, TICKER_SAGA)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.saga.processor.process_txs(wallet_address, elems, exporter)

    return exporter


@set_ibc_cache()
def txhistory(wallet_address):
    """ Configure localconfig based on options dictionary. """
    progress = ProgressSaga()
    exporter = Exporter(wallet_address, localconfig, TICKER_SAGA)
    txdata = _txdata()

    # Fetch/add genesis airdrop to csv
    progress.report_message("Getting genesis airdrop amount...")
    genesis_airdrop(wallet_address, exporter)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.saga.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
