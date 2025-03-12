import logging

from staketaxcsv import settings_csv as co
from staketaxcsv.common.ExporterTypes import FORMATS

import staketaxcsv.report_algo
import staketaxcsv.report_akt
import staketaxcsv.report_arch
import staketaxcsv.report_atom
import staketaxcsv.report_bld
import staketaxcsv.report_btsg
import staketaxcsv.report_cosmosplus
import staketaxcsv.report_dvpn
import staketaxcsv.report_dydx
import staketaxcsv.report_dym
import staketaxcsv.report_evmos
import staketaxcsv.report_fet
import staketaxcsv.report_grav
import staketaxcsv.report_huahua
import staketaxcsv.report_inj
import staketaxcsv.report_iotex
import staketaxcsv.report_juno
import staketaxcsv.report_kuji
import staketaxcsv.report_kyve
import staketaxcsv.report_luna1
import staketaxcsv.report_luna2
import staketaxcsv.report_mntl
import staketaxcsv.report_nls
import staketaxcsv.report_ntrn
import staketaxcsv.report_osmo
import staketaxcsv.report_regen
import staketaxcsv.report_rowan
import staketaxcsv.report_saga
import staketaxcsv.report_scrt
import staketaxcsv.report_sei
import staketaxcsv.report_sol
import staketaxcsv.report_stars
import staketaxcsv.report_strd
import staketaxcsv.report_tia
import staketaxcsv.report_tori

REPORT_MODULES = {
    co.TICKER_ALGO: staketaxcsv.report_algo,
    co.TICKER_AKT: staketaxcsv.report_akt,
    co.TICKER_ARCH: staketaxcsv.report_arch,
    co.TICKER_ATOM: staketaxcsv.report_atom,
    co.TICKER_BLD: staketaxcsv.report_bld,
    co.TICKER_BTSG: staketaxcsv.report_btsg,
    co.TICKER_COSMOSPLUS: staketaxcsv.report_cosmosplus,
    co.TICKER_DVPN: staketaxcsv.report_dvpn,
    co.TICKER_DYDX: staketaxcsv.report_dydx,
    co.TICKER_DYM: staketaxcsv.report_dym,
    co.TICKER_EVMOS: staketaxcsv.report_evmos,
    co.TICKER_FET: staketaxcsv.report_fet,
    co.TICKER_GRAV: staketaxcsv.report_grav,
    co.TICKER_HUAHUA: staketaxcsv.report_huahua,
    co.TICKER_IOTEX: staketaxcsv.report_iotex,
    co.TICKER_INJ: staketaxcsv.report_inj,
    co.TICKER_JUNO: staketaxcsv.report_juno,
    co.TICKER_KUJI: staketaxcsv.report_kuji,
    co.TICKER_KYVE: staketaxcsv.report_kyve,
    co.TICKER_LUNA1: staketaxcsv.report_luna1,
    co.TICKER_LUNA2: staketaxcsv.report_luna2,
    co.TICKER_MNTL: staketaxcsv.report_mntl,
    co.TICKER_NLS: staketaxcsv.report_nls,
    co.TICKER_NTRN: staketaxcsv.report_ntrn,
    co.TICKER_OSMO: staketaxcsv.report_osmo,
    co.TICKER_REGEN: staketaxcsv.report_regen,
    co.TICKER_ROWAN: staketaxcsv.report_rowan,
    co.TICKER_SAGA: staketaxcsv.report_saga,
    co.TICKER_SCRT: staketaxcsv.report_scrt,
    co.TICKER_SEI: staketaxcsv.report_sei,
    co.TICKER_SOL: staketaxcsv.report_sol,
    co.TICKER_STARS: staketaxcsv.report_stars,
    co.TICKER_STRD: staketaxcsv.report_strd,
    co.TICKER_TIA: staketaxcsv.report_tia,
    co.TICKER_TORI: staketaxcsv.report_tori,
}


def tickers():
    return sorted(REPORT_MODULES.keys())


def formats():
    return FORMATS


def has_csv(ticker, wallet_address):
    """ Returns True if wallet_address is valid address.

    :param ticker: ALGO|ATOM|LUNA1|LUNA2|...   [see staketaxcsv.tickers()]
    :param wallet_address: <string wallet address>
    """

    module = REPORT_MODULES[ticker]
    return module.wallet_exists(wallet_address)


def csv(ticker, wallet_address, csv_format, path=None, options=None, logs=True):
    """ Writes one CSV file, for this wallet address, in this format.

    :param ticker: ALGO|ATOM|LUNA1|LUNA2|...   [see staketaxcsv.tickers()]
    :param wallet_address: <string wallet address>
    :param csv_format: default|accointing|koinly|cointracking|... [see staketaxcsv.formats()]
    :param path: (optional) <string file path> .  By default, writes to /tmp .
    :param options: (optional) dictionary [documentation not in great state; see parse_args() in
           https://github.com/hodgerpodger/staketaxcsv/blob/main/src/staketaxcsv/common/report_util.py]
    :param logs: (optional) show logging.  Defaults to True.

    """
    path = path if path else "/tmp/{}.{}.{}.csv".format(ticker, wallet_address, csv_format)
    options = options if options else {}
    if logs:
        logging.basicConfig(level=logging.INFO)

    # Run report
    module = REPORT_MODULES[ticker]
    module.read_options(options)
    exporter = module.txhistory(wallet_address)
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
    :param dirpath: (optional) <string directory path> directory to write CSV files to.
                     By default, writes to /tmp .
    :param options: (optional)
    :param logs: (optional) show logging.  Defaults to True.
    """
    dirpath = dirpath if dirpath else "/tmp"
    options = options if options else {}
    if logs:
        logging.basicConfig(level=logging.INFO)

    # Run report
    module = REPORT_MODULES[ticker]
    module.read_options(options)
    exporter = module.txhistory(wallet_address)
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
    module.read_options(options)
    exporter = module.txone(wallet_address, txid)

    if csv_format == "":
        exporter.export_print()
    elif csv_format == "test":
        return exporter.export_for_test()
    else:
        exporter.export_print()
        path = path if path else "/tmp/{}.{}.csv".format(txid, csv_format)
        exporter.export_format(csv_format, path)


def historical_balances(ticker, wallet_address, path=None, options=None, logs=""):
    """ Writes historical balances CSV file for this wallet_address

        :param ticker: ALGO|ATOM|LUNA1|LUNA2|...   [see staketaxcsv.tickers()]
        :param wallet_address: <string wallet address>
        :param path: (optional) <string file path> .  By default, writes to /tmp .
        :param options: (optional) dictionary [documentation not in great state; see parse_args() in
               https://github.com/hodgerpodger/staketaxcsv/blob/main/src/staketaxcsv/common/report_util.py]
        :param logs: ""|"test"
    """
    path = path if path else f"/tmp/{ticker}.{wallet_address}.balances_historical.csv"
    options = options if options else {}

    module = REPORT_MODULES[ticker]

    if hasattr(module, staketaxcsv.report_akt.balhistory.__name__):
        module.read_options(options)
        bal_exporter = module.balhistory(wallet_address)
        if not bal_exporter:
            raise Exception("balhistory() did not return ExporterBalance object")

        if logs == "test":
            return bal_exporter.export_for_test()
        else:
            bal_exporter.export_csv(path)
    else:
        logging.error("No balhistory() function found for module=%s", str(module))
