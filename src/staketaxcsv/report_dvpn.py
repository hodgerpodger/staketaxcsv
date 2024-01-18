"""
usage: python3 staketaxcsv/report_dvpn.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/DVPN*.csv

"""

import logging

import staketaxcsv.common.ibc.api_rpc
import staketaxcsv.common.ibc.constants
import staketaxcsv.dvpn.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ibc.api_rpc import RpcAPI
from staketaxcsv.dvpn.config_dvpn import localconfig
from staketaxcsv.dvpn.progress_dvpn import LCD_SECONDS_PER_PAGE, ProgressDvpn
from staketaxcsv.settings_csv import DVPN_NODE, DVPN_NODE_RPC, TICKER_DVPN
from staketaxcsv.common.ibc import api_lcd
from staketaxcsv.common.ibc.decorators import set_ibc_cache


def main():
    report_util.main_default(TICKER_DVPN)


def read_options(options):
    """ Configure localconfig based on options dictionary. """
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(DVPN_NODE).account_exists(wallet_address)


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return LCD_SECONDS_PER_PAGE * api_lcd.get_txs_pages_count(DVPN_NODE, wallet_address, max_txs)


def txone(wallet_address, txid):
    elem = api_lcd.make_lcd_api(DVPN_NODE).get_tx(txid)

    if not elem:
        elem = RpcAPI(DVPN_NODE_RPC).get_tx(txid)
        staketaxcsv.common.ibc.api_rpc.normalize_rpc_txns(DVPN_NODE_RPC, [elem])

    exporter = Exporter(wallet_address, localconfig, TICKER_DVPN)
    txinfo = staketaxcsv.dvpn.processor.process_tx(wallet_address, elem, exporter)

    return exporter


@set_ibc_cache()
def txhistory(wallet_address):
    max_txs = localconfig.limit
    progress = ProgressDvpn()
    exporter = Exporter(wallet_address, localconfig, TICKER_DVPN)

    # LCD - fetch count of transactions to estimate progress more accurately
    lcd_count_pages = api_lcd.get_txs_pages_count(
        DVPN_NODE, wallet_address, max_txs)
    progress.set_lcd_estimate(lcd_count_pages)
    # RPC - fetch count of transactions to estimate progress more accurately
    rpc_count_pages, _ = staketaxcsv.common.ibc.api_rpc.get_txs_pages_count(
        DVPN_NODE_RPC, wallet_address, max_txs)
    progress.set_rpc_estimate(rpc_count_pages)

    # LCD - fetch transactions
    lcd_elems = api_lcd.get_txs_all(DVPN_NODE, wallet_address, max_txs, progress=progress, stage_name="lcd")

    # Some older transaction types can no longer be processed through the latest sentinelhub LCD api (version 0.9.2 at time of writing).
    # Example failure message:
    #     "unable to resolve type URL /sentinel.session.v1.MsgService/MsgStart: tx parse error: invalid request"
    #
    # Use the RPC api to backfill any transactions that were missing.
    # Only found cases of this when the address is the sender, so the `events_types` queried are limited.

    # RPC - fetch transactions
    rpc_elems = staketaxcsv.common.ibc.api_rpc.get_txs_all(
        DVPN_NODE_RPC, wallet_address, max_txs, progress=progress, stage_name="rpc",
        events_types=[staketaxcsv.common.ibc.constants.EVENTS_TYPE_SENDER])

    # See if there were any missing transactions between the LCD and RPC scans
    lcd_tx_hashes = set([e["txhash"] for e in lcd_elems])
    rpc_tx_hashes = set([e["hash"] for e in rpc_elems])
    missing_tx_hashes = frozenset(rpc_tx_hashes.difference(lcd_tx_hashes))

    elems = lcd_elems
    if missing_tx_hashes:
        progress.report_message(f"Found {len(missing_tx_hashes)} transactions from the rpc api that were missing from the lcd api")

        missing_elems = list(filter(
            lambda e, hashes=missing_tx_hashes: e["hash"] in hashes,
            rpc_elems
        ))
        staketaxcsv.common.ibc.api_rpc.normalize_rpc_txns(DVPN_NODE_RPC, missing_elems)

        elems.extend(missing_elems)

    # Process all transactions
    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.dvpn.processor.process_txs(wallet_address, elems, exporter)

    # Calculate payments from escrow to the dVPN node for bandwidth usage.
    # These payments are kept off-chain and need to be calculated through various apis provided by sentinelhub.
    progress.set_usage_payment_estimate(0)
    staketaxcsv.dvpn.processor.process_usage_payments(wallet_address, exporter)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
