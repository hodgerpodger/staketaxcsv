import argparse
import datetime
import logging
import os

from common.ExporterTypes import FORMAT_DEFAULT, FORMATS, LP_TREATMENT_CHOICES, LP_TREATMENT_TRANSFERS
from settings_csv import REPORTS_DIR, TICKER_ALGO, TICKER_ATOM, TICKER_LUNA, TICKER_OSMO, TICKER_SOL

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
        help="use Cache class (only works if dynamodb setup or class implemented)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="change to non-default max transactions limit",
    )
    if ticker in (TICKER_ALGO, TICKER_SOL):
        parser.add_argument(
            "--start_date",
            type=str,
            help="(YYYY-MM-DD) Only include transactions after start_date (inclusive)",
        )
    if ticker in (TICKER_ALGO):
        parser.add_argument(
            "--end_date",
            type=str,
            help="(YYYY-MM-DD) Only include transactions before end_date (inclusive)",
        )
    if ticker == TICKER_LUNA:
        parser.add_argument(
            "--minor_rewards",
            action="store_true",
            default=False,
            help="include minor currency rewards",
        )

    if ticker in (TICKER_LUNA, TICKER_OSMO, TICKER_ALGO):
        parser.add_argument(
            "--lp_treatment",
            choices=LP_TREATMENT_CHOICES,
            default=LP_TREATMENT_TRANSFERS,
            help="Treat LP deposits/withdrawals as transfers(default), omit, or trades. "
                 "Not applicable to koinly CSV.",
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
    if "start_date" in args and args.start_date:
        options["start_date"] = args.start_date
    if "end_date" in args and args.end_date:
        options["end_date"] = args.end_date
    if "minor_rewards" in args and args.minor_rewards:
        options["minor_rewards"] = True
    if "lp_treatment" in args and args.lp_treatment:
        options["lp_treatment"] = args.lp_treatment
    if "legacy" in args and args.legacy:
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


def export_format_for_txid(exporter, export_format, txid):
    csvpath = f"{REPORTS_DIR}/{txid}.{export_format}.csv"
    exporter.export_format(export_format, csvpath)


def read_common_options(localconfig, options):
    localconfig.job = options.get("job", None)
    localconfig.debug = options.get("debug", False)
    localconfig.cache = options.get("cache", localconfig.job is not None)
    localconfig.limit = options.get("limit", localconfig.limit)
