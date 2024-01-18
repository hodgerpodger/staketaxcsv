"""
usage: python3 staketaxcsv/report_bld.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/BLD*.csv
"""

import logging

import staketaxcsv.bld.processor
import staketaxcsv.common.ibc.api_lcd_v1
from staketaxcsv.bld.config_bld import localconfig
from staketaxcsv.bld.progress_bld import SECONDS_PER_PAGE, ProgressBld, SECONDS_PER_TX
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import BLD_NODE, TICKER_BLD, BLD_NODE_RPC
from staketaxcsv.common.ibc.tx_data import TxDataRpc
from staketaxcsv.common.ibc.decorators import set_ibc_cache
BLD_RPC_NODES = [BLD_NODE_RPC]
LIMIT_TXS_PER_QUERY = 20


def main():
    report_util.main_default(TICKER_BLD)


def read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataRpc(BLD_RPC_NODES, max_txs)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1(BLD_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_BLD)
    txinfo = staketaxcsv.bld.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    num_pages, num_txs = _txdata().get_txs_pages_count(wallet_address, progress_rpc=None, limit=LIMIT_TXS_PER_QUERY)
    return SECONDS_PER_PAGE * num_pages + SECONDS_PER_TX * num_txs


@set_ibc_cache()
def txhistory(wallet_address):
    """ Configure localconfig based on options dictionary. """
    progress = ProgressBld()
    exporter = Exporter(wallet_address, localconfig, TICKER_BLD)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    txdata.get_txs_pages_count(wallet_address, progress_rpc=progress, limit=LIMIT_TXS_PER_QUERY)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress_rpc=progress, limit=LIMIT_TXS_PER_QUERY)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.bld.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
