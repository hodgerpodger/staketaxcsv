"""
usage: python3 staketaxcsv/report_cosmosplus.py <walletaddress> --cosmosplus_node <url_lcd_node> --cosmosplus_ticker <token_symbol> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/<token_symbol>*.csv.

Notes:

* Meant to create CSV with only knowledge of LCD node and ticker (for just labeling).
* Example usage:
   python3 staketaxcsv/report_cosmosplus.py akash19yy53sz8ed88me79neeksqra06kcs5ly24758d --cosmosplus_node https://rest-akash.ecostake.com --cosmosplus_ticker AKT
* See https://github.com/cosmos/chain-registry to find LCD nodes (search "rest" in chain.json)

"""

import logging
import pprint

import staketaxcsv.cosmosplus.processor
from staketaxcsv.settings_csv import TICKER_COSMOSPLUS
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.cosmosplus.config_cosmosplus import localconfig
from staketaxcsv.cosmosplus.progress_cosmosplus import SECONDS_PER_PAGE, ProgressCosmosPlus
from staketaxcsv.common.ibc.constants import MINTSCAN_LABELS
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.tx_data import TxDataLcd
from staketaxcsv.common.ibc.decorators import set_ibc_cache


def main():
    report_util.main_default(TICKER_COSMOSPLUS)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)

    localconfig.node = options["cosmosplus_node"]
    localconfig.ticker = options.get("cosmosplus_ticker", localconfig.ticker)
    localconfig.mintscan_label = MINTSCAN_LABELS.get(localconfig.ticker, "generic")

    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    lcd_node = localconfig.node
    return TxDataLcd(lcd_node, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(localconfig.node).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_COSMOSPLUS)
    txinfo = staketaxcsv.cosmosplus.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


@set_ibc_cache()
def txhistory(wallet_address):
    progress = ProgressCosmosPlus()
    exporter = Exporter(wallet_address, localconfig, TICKER_COSMOSPLUS)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.cosmosplus.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
