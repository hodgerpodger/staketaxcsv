import logging

from staketaxcsv.settings_csv import (
    TICKER_ALGO, TICKER_ATOM, TICKER_BLD, TICKER_BTSG, TICKER_DVPN, TICKER_EVMOS, TICKER_FET,
TICKER_HUAHUA, TICKER_IOTEX, TICKER_JUNO, TICKER_KUJI, TICKER_LUNA1, TICKER_LUNA2, TICKER_OSMO,
TICKER_REGEN, TICKER_SOL, TICKER_STARS)
from staketaxcsv.common.ExporterTypes import FORMATS

import staketaxcsv.report_algo
import staketaxcsv.report_atom
import staketaxcsv.report_bld
import staketaxcsv.report_btsg
import staketaxcsv.report_dvpn
import staketaxcsv.report_evmos
import staketaxcsv.report_fet
import staketaxcsv.report_huahua
import staketaxcsv.report_iotex
import staketaxcsv.report_juno
import staketaxcsv.report_kuji
import staketaxcsv.report_luna1
import staketaxcsv.report_luna2
import staketaxcsv.report_osmo
import staketaxcsv.report_regen
import staketaxcsv.report_sol
import staketaxcsv.report_stars

REPORT_MODULES = {
    TICKER_ALGO: staketaxcsv.report_algo,
    TICKER_ATOM: staketaxcsv.report_atom,
    TICKER_BLD: staketaxcsv.report_bld,
    TICKER_BTSG: staketaxcsv.report_btsg,
    TICKER_DVPN: staketaxcsv.report_dvpn,
    TICKER_EVMOS: staketaxcsv.report_evmos,
    TICKER_FET: staketaxcsv.report_fet,
    TICKER_HUAHUA: staketaxcsv.report_huahua,
    TICKER_IOTEX: staketaxcsv.report_iotex,
    TICKER_JUNO: staketaxcsv.report_juno,
    TICKER_KUJI: staketaxcsv.report_kuji,
    TICKER_LUNA1: staketaxcsv.report_luna1,
    TICKER_LUNA2: staketaxcsv.report_luna2,
    TICKER_OSMO: staketaxcsv.report_osmo,
    TICKER_REGEN: staketaxcsv.report_regen,
    TICKER_SOL: staketaxcsv.report_sol,
    TICKER_STARS: staketaxcsv.report_stars,
}


def tickers():
    return sorted(REPORT_MODULES.keys())


def formats():
    return FORMATS


def csv(ticker, wallet_address, csv_format, path=None, options=None, logs=True):
    """ Writes one CSV file, for this wallet address, in this format.

    :param ticker: ALGO|ATOM|LUNA1|LUNA2|...   [see staketaxcsv.tickers()]
    :param wallet_address: <string wallet address>
    :param csv_format: default|accointing|koinly|cointracking|... [see staketaxcsv.formats()]
    :param path: (optional) <string file path> .  By default, writes to /tmp .
    :param options: (optional) dictionary [documentation not in great state; see parse_args() in
           https://github.com/hodgerpodger/staketaxcsv/blob/main/src/staketaxcsv/common/report_util.py]
    :params logs: (optional) show logging.  Defaults to True.

    """
    path = path if path else "/tmp/{}.{}.{}.csv".format(ticker, wallet_address, csv_format)
    options = options if options else {}
    if logs:
        logging.basicConfig(level=logging.INFO)

    # Run report
    module = REPORT_MODULES[ticker]
    module._read_options(options)
    exporter = module.txhistory(wallet_address, options)
    exporter.sort_rows()

    # Print transactions table to console
    if logs:
        exporter.export_print()

    # Write CSV
    exporter.export_format(csv_format, path)


def csv_all(ticker, wallet_address, dirpath=None, options=None, logs=True):
    """ Writes CSV files, for this wallet address, in all CSV formats.

    :param ticker: ALGO|ATOM|LUNA1|LUNA2|...   [see staketaxcsv.tickers()]
    :param wallet_address: <string wallet address>
    :params dirpath: (optional) <string directory path> directory to write CSV files to.
                     By default, writes to /tmp .
    :param options: (optional)
    :params logs: (optional) show logging.  Defaults to True.
    """
    dirpath = dirpath if dirpath else "/tmp"
    options = options if options else {}
    if logs:
        logging.basicConfig(level=logging.INFO)

    # Run report
    module = REPORT_MODULES[ticker]
    module._read_options(options)
    exporter = module.txhistory(wallet_address, options)
    exporter.sort_rows()

    # Print transactions table to console
    if logs:
        exporter.export_print()

    # Write CSVs
    for cur_format in FORMATS:
        path = "{}/{}.{}.{}.csv".format(dirpath, ticker, wallet_address, cur_format)
        exporter.export_format(cur_format, path)


def transaction(ticker, wallet_address, txid, csv_format="", path="", options=None):
    """ Print transaction to console.  If csv_format specified, writes CSV file of single transaction.

    :param ticker: ALGO|ATOM|LUNA1|LUNA2|...   [see staketaxcsv.tickers()]
    :param wallet_address: <string wallet address>
    :param txid: <string transaction id>
    :param csv_format: (optional) default|accointing|koinly|cointracking|... [see staketaxcsv.formats()]
    :param path: (optional) <string file path> .  By default, writes to /tmp .
    :param options: (optional) dictionary [documentation not in great state; see parse_args() in
           https://github.com/hodgerpodger/staketaxcsv/blob/main/src/staketaxcsv/common/report_util.py]
    """
    logging.basicConfig(level=logging.INFO)
    options = options if options else {}

    # Run report for single transaction
    module = REPORT_MODULES[ticker]
    module._read_options(options)
    exporter = module.txone(wallet_address, txid)

    # Print transactions table to console
    exporter.export_print()

    if csv_format:
        path = path if path else "/tmp/{}.{}.csv".format(txid, csv_format)
        exporter.export_format(csv_format, path)
