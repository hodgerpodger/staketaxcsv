import argparse
import datetime
import logging
import os

import staketaxcsv.api
from staketaxcsv.common.ExporterTypes import (
    FORMAT_DEFAULT, FORMATS, LP_TREATMENT_CHOICES, LP_TREATMENT_TRANSFERS)
from staketaxcsv.common.BalExporter import BALANCES_HISTORICAL
from staketaxcsv.settings_csv import (
    REPORTS_DIR, TICKER_AKT, TICKER_ALGO, TICKER_ARCH, TICKER_ATOM, TICKER_COSMOSPLUS,
    TICKER_EVMOS, TICKER_JUNO, TICKER_LUNA1, TICKER_LUNA2, TICKER_OSMO, TICKER_SAGA, TICKER_SOL, TICKER_STRD, TICKER_TIA)
from staketaxcsv import settings_csv

ALL = "all"
STAKETAX_DEBUG_CACHE = "STAKETAX_DEBUG_CACHE"
STAKETAX_CACHE = "STAKETAX_CACHE"


def main_default(ticker):
    logging.basicConfig(level=logging.INFO)

    wallet_address, export_format, txid, options = parse_args(ticker)
    run_report(ticker, wallet_address, export_format, txid, options)


def run_report(ticker, wallet_address, export_format, txid, options):
    if txid:
        path = "{}/{}.{}.csv".format(REPORTS_DIR, txid, export_format)
        staketaxcsv.api.transaction(ticker, wallet_address, txid, export_format, path, options)
    elif options.get("historical"):
        path = "{}/{}.{}.{}.csv".format(REPORTS_DIR, ticker, wallet_address, BALANCES_HISTORICAL)
        staketaxcsv.api.historical_balances(ticker, wallet_address, path, options)
    elif export_format == ALL:
        staketaxcsv.api.csv_all(ticker, wallet_address, REPORTS_DIR, options=options)
    else:
        path = "{}/{}.{}.{}.csv".format(REPORTS_DIR, ticker, wallet_address, export_format)
        staketaxcsv.api.csv(ticker, wallet_address, export_format, path, options)


def parse_args(ticker):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "wallet_address",
        help="Wallet address (not staking address)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=FORMAT_DEFAULT,
        choices=[ALL] + FORMATS,
    )
    parser.add_argument(
        "--txid",
        type=str,
        default="",
        help="If specified, runs report only on this one transaction (useful for debugging)",
    )
    parser.add_argument(
        "--historical",
        action="store_true",
        default=False,
        help="Create historical balances CSV (instead of default transactions CSV)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--debug_cache",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--dbcache",
        action="store_true",
        default=False,
        help="Force use db Cache class (requires dynamodb and overrides environment DB_CACHE)",
    )
    parser.add_argument(
        "--no_dbcache",
        action="store_true",
        default=False,
        help="Force don't use db Cache class (overrides environment DB_CACHE)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Change to non-default max transactions limit",
    )
    parser.add_argument(
        "--koinlynullmap",
        type=str,
        help="Path to the Koinly NullMap json file",
    )
    if ticker in [TICKER_AKT, TICKER_ALGO, TICKER_ARCH, TICKER_ATOM, TICKER_EVMOS,
                  TICKER_JUNO, TICKER_SAGA, TICKER_STRD, TICKER_SOL, TICKER_TIA]:
        parser.add_argument(
            "--start_date",
            type=str,
            help="(YYYY-MM-DD) Only include transactions after start_date (inclusive)",
        )
        parser.add_argument(
            "--end_date",
            type=str,
            help="(YYYY-MM-DD) Only include transactions before end_date (inclusive)",
        )
    if ticker in [TICKER_LUNA1, TICKER_OSMO, TICKER_ALGO]:
        parser.add_argument(
            "--lp_treatment",
            choices=LP_TREATMENT_CHOICES,
            default=LP_TREATMENT_TRANSFERS,
            help="Treat LP deposits/withdrawals as transfers(default), omit, or trades. "
                 "Not applicable to CSV formats with native LP transactions.",
        )
    if ticker in [TICKER_ALGO]:
        parser.add_argument(
            "--exclude_asas",
            type=str,
            help="Exclude transactions for this comma separated list of ASAs",
        )
        parser.add_argument(
            "--track_block",
            action="store_true",
            default=False,
            help="Process transactions starting from the latest block in the previous run.",
        )
    if ticker in [TICKER_COSMOSPLUS]:
        parser.add_argument(
            "--cosmosplus_node",
            type=str,
            help="Full URL of LCD/RPC node (only used in report_cosmoplus.py)"
        )
        parser.add_argument(
            "--cosmosplus_ticker",
            type=str,
            help="Symbol of token (only used in report_cosmosplus.py)"
        )
    if ticker == TICKER_LUNA1:
        parser.add_argument(
            "--minor_rewards",
            action="store_true",
            default=False,
            help="Include minor currency rewards",
        )
    if ticker == TICKER_LUNA2:
        parser.add_argument(
            "--include_tiny_vesting",
            action="store_true",
            default=False,
            help="Include tiny amounts of LUNA vesting airdrops"
        )
    if ticker in [TICKER_SOL]:
        parser.add_argument(
            "--exclude_failed",
            action="store_true",
            default=False,
            help="Exclude failed transactions"
        )
        parser.add_argument(
            "--exclude_associated",
            action="store_true",
            default=False,
            help="Exclude associated token accounts' transactions "
                 "(useful if intractable # of associated accounts)"
        )

    args = parser.parse_args()

    options = {}
    if args.historical:
        options["historical"] = args.historical
    if args.debug:
        options["debug"] = True
        logging.basicConfig(level=logging.DEBUG)
    if args.debug_cache:
        os.environ[STAKETAX_DEBUG_CACHE] = "1"
    if args.dbcache:
        settings_csv.DB_CACHE = True
    if args.no_dbcache:
        settings_csv.DB_CACHE = False
    if args.limit:
        options["limit"] = args.limit
    if args.koinlynullmap:
        options["koinlynullmap"] = args.koinlynullmap
    if "start_date" in args and args.start_date:
        options["start_date"] = args.start_date
    if "end_date" in args and args.end_date:
        options["end_date"] = args.end_date
    if "minor_rewards" in args and args.minor_rewards:
        options["minor_rewards"] = True
    if "lp_treatment" in args and args.lp_treatment:
        options["lp_treatment"] = args.lp_treatment
    if "exclude_asas" in args and args.exclude_asas:
        options["exclude_asas"] = args.exclude_asas
    if "track_block" in args and args.track_block:
        options["track_block"] = True
    if "cosmosplus_node" in args:
        options["cosmosplus_node"] = args.cosmosplus_node
    if "cosmosplus_ticker" in args:
        options["cosmosplus_ticker"] = args.cosmosplus_ticker
    if "exclude_failed" in args:
        options["exclude_failed"] = args.exclude_failed
    if "exclude_associated" in args:
        options["exclude_associated"] = args.exclude_associated
    if "include_tiny_vesting" in args:
        options["include_tiny_vesting"] = args.include_tiny_vesting

    return args.wallet_address, args.format, args.txid, options


def read_common_options(localconfig, options):
    localconfig.job = options.get("job", None)
    localconfig.debug = options.get("debug", False)
    localconfig.limit = options.get("limit", localconfig.limit)
    localconfig.koinlynullmap = options.get("koinlynullmap", localconfig.koinlynullmap)
