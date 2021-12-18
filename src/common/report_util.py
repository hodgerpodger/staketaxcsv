
import argparse
import logging
import os
from settings_csv import REPORTS_DIR

FORMAT_DEFAULT = "default"
FORMAT_COINTRACKING = "cointracking"
FORMAT_COINTRACKER = "cointracker"
FORMAT_KOINLY = "koinly"
FORMAT_CALCULATOR = "calculator"
FORMAT_ACCOINTING = "accointing"
FORMAT_TOKENTAX = "tokentax"
FORMAT_ZENLEDGER = "zenledger"
FORMATS = [FORMAT_DEFAULT, FORMAT_COINTRACKING, FORMAT_COINTRACKER, FORMAT_KOINLY, FORMAT_CALCULATOR,
           FORMAT_ACCOINTING, FORMAT_TOKENTAX, FORMAT_ZENLEDGER]
ALL = "all"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('wallet_address', help='wallet address (not staking address)')
    parser.add_argument('--format', type=str, default=FORMAT_DEFAULT, choices=FORMATS + [ALL])
    parser.add_argument('--txid', type=str, default="",
                        help='If specified, runs report only on this one transaction (useful for debugging)')

    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--cache', action='store_true', default=False,
                        help="use Cache class (only work if implemented)")
    parser.add_argument('--minor_rewards', action='store_true', default=False,
                        help="(LUNA only) include minor currency rewards")
    parser.add_argument("--lp", action="store_true", default=False,
                        help="(LUNA only) if set, treat LP deposits/withdrawals as trades "
                             "(default is treat as _LP_DEPOSIT/_LP_WITHDRAW transactions)")
    parser.add_argument("--limit", type=int,
                        help="change to non-default max transactions limit")

    args = parser.parse_args()

    options = {}
    if args.debug:
        options["debug"] = True
        logging.basicConfig(level=logging.DEBUG)
    if args.cache:
        options["cache"] = True
    if args.minor_rewards:
        options["minor_rewards"] = True
    if args.lp:
        options["lp"] = True
    if args.limit:
        options["limit"] = args.limit

    return args.wallet_address, args.format, args.txid, options


def run_exports(ticker, wallet_address, exporter, format):
    if not os.path.exists(REPORTS_DIR):
        os.mkdir(REPORTS_DIR)
    exporter.sort_rows()

    # Print transactions table to console
    exporter.export_print()

    # Get list of CSVs to write
    formats_list = FORMATS if format == ALL else [format]

    for cur_format in formats_list:
        # Write one csv
        csvpath = "{}/{}.{}.{}.csv".format(REPORTS_DIR, ticker, wallet_address, cur_format)
        if cur_format == FORMAT_DEFAULT:
            exporter.export_default_csv(csvpath)
            # Write balance-after-each-transaction csv
            csvpath2 = "{}/{}.{}.{}.csv".format(REPORTS_DIR, ticker, wallet_address, "balances")
            exporter.export_balances_csv(csvpath2)
        elif cur_format == FORMAT_COINTRACKING:
            exporter.export_cointracking_csv(csvpath)
        elif cur_format == FORMAT_COINTRACKER:
            exporter.export_cointracker_csv(csvpath)
        elif cur_format == FORMAT_KOINLY:
            exporter.export_koinly_csv(csvpath)
        elif cur_format == FORMAT_CALCULATOR:
            exporter.export_calculator_csv(csvpath)
        elif cur_format == FORMAT_ACCOINTING:
            xlsxpath = "{}/{}.{}.{}.xlsx".format(REPORTS_DIR, ticker, wallet_address, cur_format)
            exporter.export_accointing_csv(csvpath)
            exporter.convert_csv_to_xlsx(csvpath, xlsxpath)
        elif cur_format == FORMAT_TOKENTAX:
            exporter.export_tokentax_csv(csvpath)
        elif cur_format == FORMAT_ZENLEDGER:
            exporter.export_zenledger_csv(csvpath)
