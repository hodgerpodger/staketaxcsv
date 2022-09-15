"""
usage: python3 report_evmos.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/EVMOS*.csv

Note:
    * <walletaddress> can be either of 'evmos...' or '0x...' formats
"""

import logging
import pprint

import staketaxcsv.common.address
import staketaxcsv.common.ibc.api_lcd
import staketaxcsv.evmos.processor
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.ExporterTypes import FORMAT_DEFAULT
from staketaxcsv.evmos.config_evmos import localconfig
from staketaxcsv.evmos.progress_evmos import SECONDS_PER_PAGE, ProgressEVMOS
from staketaxcsv.settings_csv import EVMOS_NODE, TICKER_EVMOS


def main():
    wallet_address, export_format, txid, options = report_util.parse_args(TICKER_EVMOS)

    # Use "evmos..." format for wallet_address before proceeding with rest of script
    wallet_address, hex_address = all_address_formats(wallet_address)
    logging.info("wallet_address: %s, hex_address: %s", wallet_address, hex_address)

    if txid:
        _read_options(options)
        exporter = txone(wallet_address, txid)
        exporter.export_print()
        if export_format != FORMAT_DEFAULT:
            report_util.export_format_for_txid(exporter, export_format, txid)
    else:
        exporter = txhistory(wallet_address, options)
        report_util.run_exports(TICKER_EVMOS, wallet_address, exporter, export_format)


def all_address_formats(wallet_address):
    """ Returns ('evmos...', '0x...') given wallet_address in either format """
    if wallet_address.startswith("0x"):
        bech32_address = staketaxcsv.common.address.from_hex_to_bech32("evmos", wallet_address)
        return bech32_address, wallet_address
    elif wallet_address.startswith("evmos"):
        hex_address = staketaxcsv.common.address.from_bech32_to_hex("evmos", wallet_address)
        return wallet_address, hex_address
    else:
        return None, None


def _read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return staketaxcsv.common.ibc.api_lcd.LcdAPI(EVMOS_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = staketaxcsv.common.ibc.api_lcd.LcdAPI(EVMOS_NODE).get_tx(txid)

    print("Transaction data:")
    pprint.pprint(elem)

    exporter = Exporter(wallet_address, localconfig, TICKER_EVMOS)
    txinfo = staketaxcsv.evmos.processor.process_tx(wallet_address, elem, exporter)
    txinfo.print()
    return exporter


def estimate_duration(wallet_address, options):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(EVMOS_NODE, wallet_address, max_txs)


def txhistory(wallet_address, options):
    # Configure localconfig based on options
    _read_options(options)
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressEVMOS()
    exporter = Exporter(wallet_address, localconfig, TICKER_EVMOS)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = staketaxcsv.common.ibc.api_lcd.get_txs_pages_count(EVMOS_NODE, wallet_address, max_txs, debug=localconfig.debug)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = staketaxcsv.common.ibc.api_lcd.get_txs_all(EVMOS_NODE, wallet_address, progress, max_txs, debug=localconfig.debug)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.evmos.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
