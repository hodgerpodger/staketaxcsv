"""
usage: python3 staketaxcsv/report_cosmosplus2.py <walletaddress> --v2_ticker <token_symbol>
--v2_mintscan_label <label> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/<token_symbol>*.csv.

Notes:

* See https://docs.cosmostation.io/apis#supported-chain-list for list of supported chains

* For v2_mintscan_label, use network name used in mintscan api (i.e. use 'stargaze' if mintscan
  explorer address is https://www.mintscan.io/stargaze/)

* Example:
```
python staketaxcsv/report_cosmosplus2.py akash1cjq9r5esl9kanpkp2ww3narhn74fl62vd3z67k --v2_ticker AKT
 --v2_mintscan_label akash
```

* Uses mintscan api for transaction data source

"""

import logging

import staketaxcsv.cosmosplus2.processor
from staketaxcsv.settings_csv import TICKER_COSMOSPLUS2
from staketaxcsv.common import report_util
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.cosmosplus2.config_cosmosplus2 import localconfig
from staketaxcsv.common.ibc import api_lcd, historical_balances
from staketaxcsv.common.ibc.tx_data import TxDataMintscan
from staketaxcsv.common.ibc.decorators import set_ibc_cache
from staketaxcsv.common.ibc.progress_mintscan import ProgressMintScan, SECONDS_PER_PAGE
from staketaxcsv.common.ibc.api_mintscan_v1 import MintscanAPI


def main():
    report_util.main_default(TICKER_COSMOSPLUS2)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)

    localconfig.mintscan_label = options["v2_mintscan_label"]
    localconfig.node = f"https://apis.mintscan.io/{localconfig.mintscan_label}/lcd"
    localconfig.ticker = options.get("v2_ticker", localconfig.ticker)

    MintscanAPI.add_network(localconfig.ticker, localconfig.mintscan_label)

    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    ticker = localconfig.ticker
    return TxDataMintscan(ticker, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(localconfig.node).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, localconfig.ticker)
    txinfo = staketaxcsv.cosmosplus2.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address)


@set_ibc_cache()
def txhistory(wallet_address):
    start_date, end_date = localconfig.start_date, localconfig.end_date
    progress = ProgressMintScan(localconfig)
    exporter = Exporter(wallet_address, localconfig, localconfig.ticker)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address, start_date, end_date)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress, start_date, end_date)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.cosmosplus2.processor.process_txs(wallet_address, elems, exporter)

    return exporter


def balhistory(wallet_address):
    """ Writes historical balances CSV rows to BalExporter object """
    start_date, end_date = localconfig.start_date, localconfig.end_date
    max_txs = localconfig.limit

    exporter = historical_balances.via_mintscan(
        localconfig.node, localconfig.ticker, wallet_address, max_txs, start_date, end_date)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
