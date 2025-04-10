"""
usage: python3 staketaxcsv/report_juno.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/JUNO*.csv

TODO: JUNO CSVs are only in experimental state.  All "execute contract" transactions are still treated as
      unknown transactions.
"""

import logging

import staketaxcsv.common.ibc.api_lcd_v1
import staketaxcsv.common.ibc.api_rpc
import staketaxcsv.common.ibc.api_rpc_multinode
import staketaxcsv.juno.processor
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common import report_util
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.juno.config_juno import localconfig
from staketaxcsv.settings_csv import JUNO_NODE, TICKER_JUNO, JUNO_NODES_RPC
from staketaxcsv.common.ibc.tx_data import TxDataRpc
from staketaxcsv.common.ibc.decorators import set_ibc_cache
from staketaxcsv.juno.progress_juno import ProgressJuno, SECONDS_PER_TX, SECONDS_PER_PAGE


def main():
    report_util.main_default(TICKER_JUNO)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    localconfig.start_date = options.get("start_date", None)
    localconfig.end_date = options.get("end_date", None)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataRpc(JUNO_NODES_RPC, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(JUNO_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_JUNO)
    txinfo = staketaxcsv.juno.processor.process_tx(wallet_address, elem, exporter)

    if localconfig.debug:
        txinfo.print()

    return exporter


def estimate_duration(wallet_address):
    num_pages, num_txs =_txdata().get_txs_pages_count(wallet_address)
    return SECONDS_PER_PAGE * num_pages + SECONDS_PER_TX * num_txs


@set_ibc_cache()
def txhistory(wallet_address):
    progress = ProgressJuno()
    exporter = Exporter(wallet_address, localconfig, TICKER_JUNO)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    txdata.get_txs_pages_count(wallet_address, progress)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.juno.processor.process_txs(wallet_address, elems, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
