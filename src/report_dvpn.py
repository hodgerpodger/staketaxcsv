"""
usage: python3 report_dvpn.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/DVPN*.csv

"""

import logging
import pprint

import staketaxcsv.common.ibc.api_common
import staketaxcsv.common.ibc.api_lcd
import staketaxcsv.common.ibc.api_rpc
import staketaxcsv.dvpn.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import FORMAT_DEFAULT
from staketaxcsv.common.ibc.api_rpc import RpcAPI
from staketaxcsv.dvpn.config_dvpn import localconfig
from staketaxcsv.dvpn.progress_dvpn import LCD_SECONDS_PER_PAGE, ProgressDvpn
from staketaxcsv.settings_csv import DVPN_LCD_NODE, DVPN_RPC_NODE, TICKER_DVPN


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_DVPN)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_DVPN, wallet_address, exporter, export_format)


def _read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd.LcdAPI(DVPN_LCD_NODE).account_exists(wallet_address)


def estimate_duration(wallet_address, options):
    max_txs = localconfig.limit
    return LCD_SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(DVPN_LCD_NODE, wallet_address, max_txs)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_lcd.LcdAPI(DVPN_LCD_NODE).get_tx(txid)
    if not elem:
        elem = RpcAPI(DVPN_RPC_NODE).get_tx(txid)
        staketaxcsv.common.ibc.api_rpc.normalize_rpc_txns(DVPN_RPC_NODE, [elem])

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_DVPN)
    txinfo = staketaxcsv.dvpn.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressDvpn()
    exporter = Exporter(wallet_address, localconfig, TICKER_DVPN)

    # LCD - fetch count of transactions to estimate progress more accurately
    lcd_count_pages = staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(DVPN_LCD_NODE, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_lcd_estimate(lcd_count_pages)
    # RPC - fetch count of transactions to estimate progress more accurately
    rpc_count_pages = staketaxcsv.common.ibc.api_rpc.get_txs_pages_count(DVPN_RPC_NODE, wallet_address, max_txs,
                                                             debug=localconfig.debug)
    progress.set_rpc_estimate(rpc_count_pages)

    # LCD - fetch transactions
    lcd_elems = staketaxcsv.common.ibc.api_lcd.get_txs_all(DVPN_LCD_NODE, wallet_address, progress, max_txs,
                                               debug=localconfig.debug,
                                               stage_name="lcd"
                                               )

    # Some older transaction types can no longer be processed through the latest sentinelhub LCD api (version 0.9.2 at time of writing).
    # Example failure message:
    #     "unable to resolve type URL /sentinel.session.v1.MsgService/MsgStart: tx parse error: invalid request"
    #
    # Use the RPC api to backfill any transactions that were missing.
    # Only found cases of this when the address is the sender, so the `events_types` queried are limited.

    # RPC - fetch transactions
    rpc_elems = staketaxcsv.common.ibc.api_rpc.get_txs_all(DVPN_RPC_NODE, wallet_address, progress, max_txs,
                                               debug=localconfig.debug,
                                               stage_name="rpc",
                                               events_types=[staketaxcsv.common.ibc.api_common.EVENTS_TYPE_SENDER]
                                               )

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
        staketaxcsv.common.ibc.api_rpc.normalize_rpc_txns(DVPN_RPC_NODE, missing_elems)

        elems.extend(missing_elems)

    # Process all transactions
    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.dvpn.processor.process_txs(wallet_address, elems, exporter)

    # Calculate payments from escrow to the dVPN node for bandwidth usage.
    # These payments are kept off-chain and need to be calculated through various apis provided by sentinelhub.
    progress.set_usage_payment_estimate(0)
    staketaxcsv.dvpn.processor.process_usage_payments(wallet_address, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)

    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
