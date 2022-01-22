import argparse
import logging
import os

from common.ExporterTypes import FORMAT_DEFAULT, FORMATS
from settings_csv import REPORTS_DIR, TICKER_ATOM, TICKER_LUNA, TICKER_OSMO

ALL = "all"


def parse_args(ticker):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "wallet_address",
        help="wallet address (not staking address)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=FORMAT_DEFAULT,
        choices=FORMATS + [ALL],
    )
    parser.add_argument(
        "--txid",
        type=str,
        default="",
        help="If specified, runs report only on this one transaction (useful for debugging)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        default=False,
        help="use Cache class (only work if implemented)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="change to non-default max transactions limit",
    )
    if ticker == TICKER_LUNA:
        parser.add_argument(
            "--minor_rewards",
            action="store_true",
            default=False,
            help="include minor currency rewards",
        )
    if ticker in (TICKER_LUNA, TICKER_OSMO):
        parser.add_argument(
            "--lp_transfers",
            action="store_true",
            default=False,
            help="treat LP deposits/withdrawals as transfers (default is non-exportable custom tx)",
        )
    if ticker in (TICKER_LUNA, TICKER_OSMO):
        parser.add_argument(
            "--lp_trades",
            action="store_true",
            default=False,
            help="treat LP deposits/withdrawals as trades (default is non-exportable custom tx)",
        )
    if ticker == TICKER_ATOM:
        parser.add_argument(
            "--legacy",
            action="store_true",
            default=False,
            help="include legacy transactions for cosmoshub-3",
        )

    args = parser.parse_args()

    options = {}
    if args.debug:
        options["debug"] = True
        logging.basicConfig(level=logging.DEBUG)
    if args.cache:
        options["cache"] = True
    if args.limit:
        options["limit"] = args.limit
    if "minor_rewards" in args:
        options["minor_rewards"] = True
    if "lp_transfers" in args:
        options["lp_transfers"] = True
    if "lp_trades" in args:
        options["lp_trades"] = True
    if "legacy" in args:
        options["legacy"] = True

    return args.wallet_address, args.format, args.txid, options


def run_exports(ticker, wallet_address, exporter, export_format):
    if not os.path.exists(REPORTS_DIR):
        os.mkdir(REPORTS_DIR)
    exporter.sort_rows()

    # Print transactions table to console
    exporter.export_print()

    # Get list of CSVs to write
    formats_list = FORMATS if export_format == ALL else [export_format]

    for cur_format in formats_list:
        # Write one csv
        csvpath = f"{REPORTS_DIR}/{ticker}.{wallet_address}.{cur_format}.csv"
        exporter.export_format(cur_format, csvpath)
