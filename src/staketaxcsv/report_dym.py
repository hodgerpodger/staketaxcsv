"""
usage: python3 staketaxcsv/report_dym.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/DYM*.csv

Note:
    * <walletaddress> can be either of 'dym...' or '0x...' formats
"""

import logging

import staketaxcsv.dym.processor
from staketaxcsv.common.address import dym_addrs
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.decorators import set_ibc_cache
from staketaxcsv.common.ibc.tx_data import TxDataLcd
from staketaxcsv.common import report_util
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.dym.genesis_airdrop import genesis_airdrop
from staketaxcsv.dym.config_dym import localconfig
from staketaxcsv.dym.progress_dym import SECONDS_PER_PAGE, ProgressDym
from staketaxcsv.settings_csv import DYM_NODE, TICKER_DYM


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_DYM)

    # Use "dym..." format for wallet_address before proceeding with rest of script
    wallet_address, hex_address = dym_addrs(wallet_address)
    logging.info("wallet_address: %s, hex_address: %s", wallet_address, hex_address)

    report_util.run_report(TICKER_DYM, wallet_address, export_format, txid, options)


def read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataLcd(DYM_NODE, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(DYM_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_DYM)
    txinfo = staketaxcsv.dym.processor.process_tx(wallet_address, elem, exporter)

    if localconfig.debug:
        print("txinfo:")
        txinfo.print()

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


@set_ibc_cache()
def txhistory(wallet_address):
    """ Configure localconfig based on options dictionary. """
    progress = ProgressDym()
    exporter = Exporter(wallet_address, localconfig, TICKER_DYM)
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
    staketaxcsv.dym.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
